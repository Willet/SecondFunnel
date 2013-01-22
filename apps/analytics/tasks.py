"""
Analytics protector bunny:

 ()()
 (-_-)
 (()())

"""
import pickle, sys

from datetime import date, datetime

from functools import partial

from celery import task, subtask
from oauth2client.client import SignedJwtAssertionCredentials

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from apps.analytics.storage_backends import GoogleAnalyticsBackend
from apps.analytics.models import (AnalyticsRecency, Category, Metric, KVStore,
    SharedStorage)
from apps.assets.models import Store, Product
from apps.pinpoint.models import Campaign


# Helper methods used by the tasks below
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


def get_oldest_analytics_date():
    """Figure out earliest date for which we're missing analytics data"""

    oldest_analytics_data = datetime.now().date()

    # iterate through our stores and find the most out of sync
    stores = Store.objects.all()

    for store in stores:
        store_type = ContentType.objects.get_for_model(Store)

        try:
            kv_store = KVStore.objects.get(
                content_type=store_type, object_id=store.id)

        except KVStore.DoesNotExist:
            # no pinpoint analytics data was fetched for this store
            # get everything, use the prior-to-launch date so that
            # we're sure everything is in scope

            oldest_analytics_data = date(2012, 9, 1)

            # we're done checking for dates at this point
            break

        else:
            # have recency data, see if it's older than oldest recency
            if kv_store.timestamp < oldest_analytics_data:
                oldest_analytics_data = kv_store.timestamp.date()

    return oldest_analytics_data


@task()
def redo_analytics():
    """Erases cached analytics and recency data, starts update process"""

    logger = redo_analytics.get_logger()

    logger.info("Redoing analytics")

    KVStore.objects.all().delete()
    AnalyticsRecency.objects.all().delete()

    logger.info("Removed old analytics data")

    return subtask(update_pinpoint_analytics).delay()


@task()
def update_pinpoint_analytics():
    """
    Figures out what analytics data we need,
    fetches that and initiates calculations
    """

    # Helper methods
    def row_getter(row):
        """
        Get a data column from provided row
        """

        def get(key):
            """
            Column is looked up by an index from dimensions settings
            """

            return row[ga_query_settings['dimensions'].index(key)]
        return get

    logger = update_pinpoint_analytics.get_logger()
    logger.info("Updating analytics data")

    # define what we're requesting from Google Analytics
    ga_query_settings = {
        'metrics': ['uniqueEvents'],
        'dimensions': ['eventCategory', 'eventAction', 'eventLabel', 'date'],
        'sort': ['date']
    }

    # initialize GA backend
    ga = GoogleAnalyticsBackend()

    # by default, request as much data as we can
    start_from_date = date(2012, 9, 1)

    logger.info("We need to fetch analytics data from GA starting from %s",
        start_from_date)

    raw_results = ga.results_iterator(
        # start date
        start_from_date,

        # end date
        datetime.now().date(),

        # what metric to get
        ga_query_settings['metrics'],

        # which data columns to get
        dimensions=ga_query_settings['dimensions'],

        # what to sort by
        sort=ga_query_settings['sort'],
    )

    analytics_categories = {
        'awareness': [],
        'engagement': [],
        'sharing': []
    }

    # iterate through potentially multi-page results from Google Analytics
    for data_page in raw_results:
        logger.info("Processing results page %s", data_page)

        if not data_page.get('rows'):
            logger.info("No rows available.")
            continue

        rows = data_page.get('rows')

        for row in rows:
            getter = row_getter(row)

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

            # uniqueEvents is the last item in the list
            try:
                row_data['count'] = int(row[-1])

            except ValueError:
                logger.warning(
                    "GA row data isn't what we're expecting: count=%s",
                    row[row.length - 1])
                continue

            # check that all variables in row_data are present
            all_present = all(
                # get a list of booleans for each row value
                [row_data[i] is not None for i in row_data]
            )

            if not all_present:
                logger.warning(
                    "GA row data is missing attributes, category=%s, action=%s",
                    category, action)
                continue

            if row_data['action_type'] == 'inpage':
                analytics_categories['engagement'].append(row_data)

            elif row_data['action_type'] == 'share':
                analytics_categories['sharing'].append(row_data)

    # message could be larger than 64kb. As a quick way of circumventing the limitation,
    # use "shared memory" approach to message passing
    message = SharedStorage(data=pickle.dumps(analytics_categories))
    message.save()

    # pass ID of the message to the processing task
    return subtask(save_category_data, (message.id,)).delay()


@task()
def save_category_data(message_id):
    """Processes individual data row, saves key/value
    analytics pairs for associated store and campaign"""

    def get_data_pair(store_id, campaign_id):
        return KVStore(
            content_type=store_type,
            object_id=store_id
        ), KVStore(
            content_type=campaign_type,
            object_id=campaign_id
        )

    logger = save_category_data.get_logger()

    store_type = ContentType.objects.get_for_model(Store)
    campaign_type = ContentType.objects.get_for_model(Campaign)
    product_type = ContentType.objects.get_for_model(Product)

    try:
        message = SharedStorage.objects.get(id=message_id)

    except SharedStorage.DoesNotExist:
        logger.error("Missing message with id={0}. Aborting.".format(
            message_id))
        return

    try:
        # prevent KeyError on unpickling
        data = pickle.loads(str(message.data))

    # could potentially throw a whole lot of different exceptions
    except:
        logger.error("Could not process the message with id={0}: {1}".format(
            message_id, sys.exc_info()[0]))
        return

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

            data1, data2 = get_data_pair(row['store_id'], row['campaign_id'])
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
    for updated_store_id in updated_stores:
        store_recency, recency_created = AnalyticsRecency.objects.get_or_create(
            content_type=store_type,
            object_id=updated_store_id
        )

        if not recency_created:
            store_recency.save()

    for updated_campaign_id in updated_campaigns:
        # unpacks into (instance, created)
        campaign_recency, recency_created = AnalyticsRecency.objects.get_or_create(
            content_type=campaign_type,
            object_id=updated_campaign_id
        )

        # if not created
        if not recency_created:
            campaign_recency.save()

    return subtask(process_saved_metrics).delay()


@task()
def process_saved_metrics():
    """Calculates "meta" metrics, which are combined out of "raw" saved data"""
    logger = process_saved_metrics.get_logger()

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

    to_process = [
        # Engagement
        {
            'q_filter': Q(key__startswith="inpage-"),
            'metrics': [
                # Product Interactions
                # sums up all product related interactions
                {
                    'slug': 'product-interactions',
                    'key': 'inpage-product-interactions',
                    'q_filter': Q(target_type=target_types['product']) & ~Q(meta="meta_metric"),
                },

                # sums up all content related interactions
                # TODO

                # Total Interactions
                # sums up product and content interactions
                {
                    'slug': 'total-interactions',
                    'key': 'inpage-total-interactions',
                    'q_filter': Q(key__endswith='product-interactions') | Q(key__endswith='content-interactions')
                },
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
                    'q_filter': Q(key='share-clicked')
                },
            ]
        },

        # Awareness
        # TODO
    ]

    for category in to_process:
        process_category(category)

def preprocess_row(row, logger):
    try:
        row['date'] = datetime.strptime(row['date'], "%Y%m%d")

    except (IndexError, ValueError):
        logger.warning("Date is unrecognized: %s", row['date'])

    return row
