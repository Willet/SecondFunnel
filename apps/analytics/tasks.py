"""
Analytics protector bunny:

 ()()
 (-_-)
 (()())

"""
import pickle, sys

from datetime import date, datetime

from functools import partial

from celery import task, subtask, chain
from celery.utils.log import get_task_logger
from oauth2client.client import SignedJwtAssertionCredentials

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from apps.analytics.storage_backends import GoogleAnalyticsBackend
from apps.analytics.models import (AnalyticsRecency, Category, Metric, KVStore,
    SharedStorage)
from apps.assets.models import Store, Product
from apps.pinpoint.models import Campaign


logger = get_task_logger(__name__)

# Helper functions used by the tasks below
def get_by_key(string, key):
    """
    Gets a variable stored within a Google Analytics Core API column by its key

    Column format: var1=value|var2=value
    """
    try:
        my_dict = dict((k, v) for (k, v) in (
                assignment.split("=") for assignment in string.split("|")
            )
        )

        return my_dict.get(key, None)

    except ValueError:
        return None


def get_ga_generator(query):
    """
    Constructs our own generator over pages of Google Analytics Core API results
    """
    ga = GoogleAnalyticsBackend()

    return ga.results_iterator(
        # start date
        date(2013, 1, 1),

        # end date
        datetime.now().date(),

        # what metrics to get
        query['metrics'],

        # which data columns to get
        dimensions=query['dimensions'],

        # what to sort by
        sort=query['sort']
    )


def row_getter(query, row):
    """
    Get a data column from provided row
    """

    def get(key):
        """
        Column is looked up by an index from dimensions settings
        """
        try:
            return row[query['dimensions'].index(key)]
        except ValueError:
            return row[query['metrics'].index(key) + len(query['dimensions'])]

    return get


def get_data_pair(store_type, campaign_type, store_id, campaign_id):
    return KVStore(
        content_type=store_type,
        object_id=store_id
    ), KVStore(
        content_type=campaign_type,
        object_id=campaign_id
    )


def get_message_by_id(message_id):
    try:
        message = SharedStorage.objects.get(id=message_id)

    except SharedStorage.DoesNotExist:
        logger.error("Missing message with id={0}. Aborting.".format(
            message_id))
        return None, None

    try:
        # str() prevents KeyError on unpickling
        data = pickle.loads(str(message.data))

    # could potentially throw a whole lot of different exceptions
    except:
        logger.error("Could not process message with id={0}: {1}".format(
            message_id, sys.exc_info()[0]))
        return None, None

    return data, message


def update_recency(object_type, object_id):
    recency, recency_created = AnalyticsRecency.objects.get_or_create(
        content_type=object_type,
        object_id=object_id
    )

    if not recency_created:
        recency.save()


def preprocess_row(row, logger):
    try:
        row['date'] = datetime.strptime(row['date'], "%Y%m%d")

    except (IndexError, ValueError):
        logger.warning("Date is unrecognized: %s", row['date'])

    return row


class Categories:
    """
    Caches analytics categories internally while providing useful shortcuts.
    Available keys per category slug:
    - instance: model instance
    - metric: function, takes metric slug and returns metric instance
              if metric does not exist, throws an exception
    """

    def __init__(self):
        self.inner_list = {}

    def get(self, category_slug):
        if category_slug not in self.inner_list:
            try:
                obj = Category.objects.prefetch_related(
                    'metrics').get(slug=category_slug, enabled=True)

                self.inner_list[category_slug] = {
                    'instance': obj,
                    'metric': lambda metric: obj.metrics.get(
                        slug=metric, enabled=True)
                }

            except Category.DoesNotExist:
                raise LookupError(
                    "Category %s not setup in the database" % category_slug
                )

        return self.inner_list[category_slug]


@task()
def redo_analytics():
    """Erases cached analytics and recency data, starts update process"""
    logger.info("Redoing analytics")

    KVStore.objects.all().delete()
    AnalyticsRecency.objects.all().delete()

    logger.info("Removed old analytics data")

    task_chain = chain(fetch_awareness_data.s(), process_awareness_data.s(),
                     fetch_event_data.s(), process_event_data.s(),
                     aggregate_saved_metrics.s())

    task_chain.delay()


@task()
def fetch_awareness_data(*args):
    logger.info("Updating awareness analytics data")

    query = {
        'metrics': ['visitors', 'pageviews'],
        'dimensions': ['date', 'customVarValue1', 'customVarValue2'],
        'sort': ['date']
    }

    fetched_rows = []
    raw_results = get_ga_generator(query)

    for data_page in raw_results:
        rows = data_page.get('rows')

        if not rows:
            logger.info("No rows available.")
            continue

        for row in rows:
            getter = row_getter(query, row)

            row_data = {
                'date': getter('date'),
                'store_id': getter('customVarValue1'),
                'campaign_id': getter('customVarValue2'),
                'visitors': getter('visitors'),
                'pageviews': getter('pageviews'),
            }

            all_present = all(
                # get a list of booleans for each row value
                [row_data[key] is not None for key in row_data]
            )

            if not all_present:
                logger.warning(
                    "GA row data is missing attributes: {0}".format(row_data))
                continue

            fetched_rows.append(row_data)

    # message could be larger than 64kb. As a quick way of circumventing the limitation,
    # use "shared memory" approach to message passing
    message = SharedStorage(data=pickle.dumps(fetched_rows))
    message.save()

    # pass ID of the message to the processing task
    return message.id


@task()
def fetch_event_data(*args):
    """
    Figures out what analytics data we need,
    fetches that and initiates calculations
    """
    logger.info("Updating event analytics data")
    engagement_prefixes = ["inpage", "visit", "content"]
    share_prefixes = ["share"]

    query = {
        'metrics': ['uniqueEvents'],
        'dimensions': ['eventCategory', 'eventAction', 'eventLabel', 'date'],
        'sort': ['date']
    }

    raw_results = get_ga_generator(query)

    analytics_categories = {
        'engagement': [],
        'sharing': []
    }

    # iterate through potentially multi-page results from Google Analytics
    for data_page in raw_results:
        rows = data_page.get('rows')

        if not rows:
            logger.info("No rows available.")
            continue

        for row in rows:
            getter = row_getter(query, row)

            category = getter('eventCategory')
            action = getter('eventAction')

            row_data = {
                'label':            getter('eventLabel'),
                'date':             getter('date'),
                # 'value':          getter('eventValue'),

                'store_id':         get_by_key(category, "storeid"),
                'campaign_id':      get_by_key(category, "campaignid"),
                'referrer':         get_by_key(category, "referrer"),
                'domain':           get_by_key(category, "domain"),

                'action_type':      get_by_key(action, "actionType"),
                'action_subtype':   get_by_key(action, "actionSubtype"),
                'action_scope':     get_by_key(action, "actionScope"),
                'network':          get_by_key(action, "network"),
            }

            # store_id could be a record ID or a slug :/
            try:
                int(row_data['store_id'])

            # it's a slug!
            except ValueError:

                try:
                    row_data['store_id'] = Store.objects.get(
                        slug=row_data['store_id']).id

                except Store.DoesNotExist:
                    logger.error("Store with id={0} does not exist. Skipping.".format(
                        row_data['store_id']))

                    continue

            # it's neither
            except TypeError:
                logger.error("Received invalid store id={0}".format(
                    row_data['store_id']))
                continue

            # uniqueEvents is the last item in the list
            try:
                row_data['count'] = int(row[-1])

            except ValueError:
                logger.warning(
                    "GA row data isn't what we're expecting: count={0}".format(
                        row[row.length - 1]))
                continue

            # check that all variables in row_data are present
            all_present = all(
                # get a list of booleans for each row value
                [row_data[i] is not None for i in row_data]
            )

            if not all_present:
                logger.warning(
                    "GA row data is missing attributes, category={0}, action={1}".format(
                    category, action))
                continue

            if row_data['action_type'] in engagement_prefixes:
                analytics_categories['engagement'].append(row_data)

            elif row_data['action_type'] in share_prefixes:
                analytics_categories['sharing'].append(row_data)

    # message could be larger than 64kb. As a quick way of circumventing the limitation,
    # use "shared memory" approach to message passing
    message = SharedStorage(data=pickle.dumps(analytics_categories))
    message.save()

    # pass ID of the message to the processing task
    return message.id


@task()
def process_awareness_data(message_id):
    """Processes fetched awareness data, row by row"""
    def save_data_pair(store_type, campaign_type, category, row, column):
        data1, data2 = get_data_pair(store_type, campaign_type, row['store_id'], row['campaign_id'])
        data1.key = data2.key = "{0}-{1}".format("awareness", column)
        data1.value = data2.value = row[column]
        data1.timestamp = data2.timestamp = row['date']

        data1.save()
        data2.save()

        try:
            category['metric'](data1.key).data.add(data1, data2)

        except Metric.DoesNotExist:
            data1.delete()
            data2.delete()
            logger.error(
                "Error saving metrics: {0}, {1}. Metric {2} is not in db".format(
                data1, data2, data1.key
            ))

    store_type = ContentType.objects.get_for_model(Store)
    campaign_type = ContentType.objects.get_for_model(Campaign)

    data, message = get_message_by_id(message_id)
    if not data:
        return

    # we can safely delete the passed message at this point
    message.delete()

    updated_stores = []
    updated_campaigns = []

    categories = Categories()
    saver = partial(save_data_pair, store_type, campaign_type, categories.get("awareness"))

    columns_to_save = ["visitors", "pageviews"]

    for row in data:
        row = preprocess_row(row, logger)

        map(lambda column: saver(row, column), columns_to_save)

        if row['store_id'] not in updated_stores:
            updated_stores.append(row['store_id'])

        if row['campaign_id'] not in updated_campaigns:
            updated_campaigns.append(row['campaign_id'])

    # Update analytics recency data for all affected stores and campaigns
    recency_updater = partial(update_recency, store_type)
    map(lambda object_id: recency_updater(object_id), updated_stores)

    recency_updater = partial(update_recency, campaign_type)
    map(lambda object_id: recency_updater(object_id), updated_campaigns)

    return None

@task()
def process_event_data(message_id):
    """Processes fetched event data, row by row, saves key/value
    analytics pairs for associated store and campaign"""
    store_type = ContentType.objects.get_for_model(Store)
    campaign_type = ContentType.objects.get_for_model(Campaign)
    product_type = ContentType.objects.get_for_model(Product)

    data, message = get_message_by_id(message_id)
    if not data:
        return

    # we can safely delete the passed message at this point
    message.delete()

    updated_stores = []
    updated_campaigns = []

    categories = Categories()

    # handle sharing data
    for category_slug in data.keys():
        logger.info("Processing %s", category_slug)
        for row in data[category_slug]:
            # with each pass, we're saving a pair of KVStore objects
            # one for the specific campaign, and one for the store
            # to which the campaign belongs

            # we do this here and not in "pre processing" because celery can't
            # serialize certain things (e.g. datetime objects)
            row = preprocess_row(row, logger)

            # total sharing
            # total sharing per network
            # sharing per scope
            # sharing per scope per network
            # share vs click

            category = categories.get(category_slug)

            data1, data2 = get_data_pair(
                store_type, campaign_type, row['store_id'], row['campaign_id'])
            data1.key = data2.key = "{0}-{1}".format(
                row['action_type'], row['action_subtype'])

            data1.value = data2.value = row['count']
            data1.timestamp = data2.timestamp = row['date']

            if row['action_type'] == "share":
                data1.meta = data2.meta = row['network']
            else:
                data1.meta = data2.meta = row['action_scope']

            # we're using row['label'] to track URLs of objects acted upon.
            # Assume they're products for now, but KVStore supports generic FK
            if row['label']:
                product = Product.objects.filter(original_url=row['label'])[:1]
                if len(product) > 0:
                    # TODO: deal with multiple results?
                    # What are the use cases for this?
                    product = product[0]
                    data1.target_id = data2.target_id = product.id
                    data1.target_type = data2.target_type = product_type

                # couldn't locate a Product this event is referring to.
                # Maybe it's not a Product?
                else:
                    # @TODO deal with this case
                    pass

            data1.save()
            data2.save()

            try:
                category['metric'](data1.key).data.add(data1, data2)

            except Metric.DoesNotExist:
                data1.delete()
                data2.delete()
                logger.error(
                    "Error saving metrics: %s, %s. Metric %s is not in db",
                    data1, data2, data1.key
                )
                continue

            if row['store_id'] not in updated_stores:
                updated_stores.append(row['store_id'])

            if row['campaign_id'] not in updated_campaigns:
                updated_campaigns.append(row['campaign_id'])

    # handle engagement data
    # interactions per scope
    # clickthrough
    # open popup
    # buy now
    # share

    # Update analytics recency data for all affected stores and campaigns
    recency_updater = partial(update_recency, store_type)
    map(lambda object_id: recency_updater(object_id), updated_stores)

    recency_updater = partial(update_recency, campaign_type)
    map(lambda object_id: recency_updater(object_id), updated_campaigns)

    return None

@task()
def aggregate_saved_metrics(*args):
    """Calculates "meta" metrics, which are combined out of "raw" saved data"""
    # remove all the existing meta metric data
    KVStore.objects.filter(meta="meta_metric").delete()

    # data types for checking event targets
    target_types = {
        'product': ContentType.objects.get_for_model(Product),
    }

    def process_category(obj):
        """
        Adds a new KV, using it as a per-day summation for KV data
        defined by passed in Q filters
        """
        category_data = KVStore.objects.filter(obj['q_filter'])

        for metric_obj in obj['metrics']:
            try:
                metric = Metric.objects.get(slug=metric_obj['slug'])

            # metric isn't set up properly, try the next one
            # TODO: create metrics in code?
            except Metric.DoesNotExist:
                logger.error(
                    "Error processing metric %s. Metric is not in db",
                    metric_obj['slug']
                )
                continue

            data = category_data.filter(metric_obj['q_filter'])

            for datum in data:
                # meta-kv already present, increment
                try:
                    kv = KVStore.objects.get(
                        content_type=datum.content_type,
                        object_id=datum.object_id,
                        key=metric_obj['key'],
                        timestamp=datum.timestamp,
                        meta="meta_metric"
                    )

                    # allows for custom aggregation: average, etc
                    if 'aggregator' in metric_obj:
                        kv.value = metric_obj['aggregator'](datum.value)
                    else:
                        kv.value += datum.value

                    kv.save()

                # need to create the meta-kv
                except KVStore.DoesNotExist:
                    kv = KVStore(
                        content_type=datum.content_type,
                        object_id=datum.object_id,
                        key=metric_obj['key'],
                        value=datum.value,
                        timestamp=datum.timestamp,
                        meta="meta_metric"
                    )
                    kv.save()

                metric.data.add(kv)

    # this list defines how the data for "meta-metrics" is to be calculated
    # list is a series of categories to process

    # each category contains a lookup query to define a common dataset
    # for the metrics to work with

    # it also defines a list of metrics to process
    # each metric defines a further lookup query
    # to further narrow down the  category data

    # process_category function then does daily sums of said data

    def averager():
        values = []

        def avg(value):
            values.append(value)
            return sum(values) / float(len(values))

        return avg

    avg = averager()

    to_process = [
        # Bounces
        {
            # 1st data filter
            'q_filter': Q(key__startswith="visit-"),

            'metrics': [
                # Sum up No Bounces
                {
                    # Metric slug
                    'slug': 'total-no-bounces',

                    # KVStore key
                    'key': 'total-no-bounces',

                    # 2nd data filter
                    'q_filter': Q(key='visit-noBounce')
                }
            ]
        },

        # Engagement
        {
            # 1st data filter
            'q_filter': Q(key__startswith="inpage-") | Q(key__startswith="content-") | Q(key__startswith="product-"),

            'metrics': [
                # Product Interactions
                {
                    'slug': 'product-interactions',
                    'key': 'product-interactions',
                    'q_filter': Q(target_type=target_types['product']) & ~Q(meta="meta_metric"),
                },

                # Content Interactions
                {
                    'slug': 'content-interactions',
                    'key': 'content-interactions',
                    'q_filter': Q(key__startswith='content-') & ~Q(meta="meta_metric"),
                },

                # Total Interactions
                {
                    'slug': 'total-interactions',
                    'key': 'total-interactions',
                    'q_filter': Q(key='product-interactions') | Q(key='content-interactions')
                }
            ]
        },

        # Sharing
        {
            'q_filter': Q(key__startswith="share-"),
            'metrics': [
                # sums up all clicked-on-social-button actions
                {
                    'slug': 'total-shares',
                    'key': 'share-total',
                    'q_filter': Q(key='share-clicked') | Q(key='share-liked')
                },
            ]
        },

        # Awareness
        {
            'q_filter': Q(key__startswith="awareness-"),
            'metrics': [
                # total visitors
                {
                    'slug': 'awareness-visitors',
                    'key': 'awareness-visitors',
                    'q_filter': Q(key='awareness-visitors')
                },

                # total pageviews
                {
                    'slug': 'awareness-pageviews',
                    'key': 'awareness-pageviews',
                    'q_filter': Q(key='awareness-pageviews')
                }
            ]
        }
    ]

    for category in to_process:
        process_category(category)
