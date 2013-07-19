"""
Analytics protector bunny:

()()
(-_-)
(()())

django celery uses settings.BROKER_URL and settings.BROKER_TRANSPORT_OPTIONS.
http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html

"""
from copy import deepcopy
import pickle, sys

from datetime import date, datetime, timedelta, tzinfo

from urlparse import urlparse

# http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#defining-and-calling-tasks
from celery import task, chain, group
from celery.utils.log import get_task_logger

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
import django.db.transaction as transaction
from pytz import utc

from apps.analytics.storage_backends import GoogleAnalyticsBackend
from apps.analytics.models import (AnalyticsRecency, Category, Metric, KVStore,
    SharedStorage)
from apps.assets.models import Store, Product, GenericImage, YoutubeVideo
from apps.pinpoint.models import Campaign, IntentRankCampaign


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

    return ga.results_iterator(start_date=date(2013, 1, 1),  # start date
                               end_date=datetime.now().date(),  # end date
                               metrics=query['metrics'],  # what metrics to get
                               dimensions=query['dimensions'],  # which data columns to get
                               sort=query['sort'],  # what to sort by
                               start_index='1')


def get_column_value(query, row, key):
    """Get a data column from provided row"""
    try:
        return row[query['dimensions'].index(key)]
    except ValueError:
        return row[query['metrics'].index(key) + len(query['dimensions'])]


def target_getter(label):
    """Locates an event target based on the label passed in.
    Tries products first, then GenericImages, then Videos"""

    product_type = ContentType.objects.get_for_model(Product)
    generic_image_type = ContentType.objects.get_for_model(GenericImage)
    youtube_type = ContentType.objects.get_for_model(YoutubeVideo)

    target = Product.objects.filter(original_url=label)[:1]
    if len(target) != 0:
        return target[0].id, product_type

    # filter out S3's signature GET stuff & hostname
    try:
        # don't want the leading slash
        label = urlparse(label).path[1:]
    except AttributeError:
        pass

    target = GenericImage.objects.filter(hosted__startswith=label)[:1]
    if len(target) != 0:
        return target[0].id, generic_image_type

    target = YoutubeVideo.objects.filter(video_id=label)[:1]
    if len(target) != 0:
        return target[0].id, youtube_type

    return None, None


def save_data_pair(store_type, campaign_type, category, row, column):
    """Saves the same information for both the campaign and its store,
    presumably for read performance.
    """
    data1 = KVStore(content_type=store_type, object_id=row['store_id'])
    data2 = KVStore(content_type=campaign_type, object_id=row['campaign_id'])

    data1.key = data2.key = column['key']
    data1.value = data2.value = row[column['value']]
    data1.timestamp = data2.timestamp = row['date']

    if row[column['meta']] != "(not set)":
        data1.meta = data2.meta = row[column['meta']]

    if 'label' in row:
        object_id, object_type = target_getter(row['label'])
        if object_id is not None:
            data1.target_id = data2.target_id = object_id
            data1.target_type = data2.target_type = object_type

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


def get_message_by_id(message_id):
    """Retrieve a "SharedStorage" thing from the database.

    @return: (the message text, the message object)

    SharedStorages are used to bypass message size limits of SQS.
    """
    try:
        message = SharedStorage.objects.get(id=message_id)
    except SharedStorage.DoesNotExist:
        logger.error("Missing message with id={0}. Aborting.".format(
            message_id))
        return (None, None)

    try:
        # str() prevents KeyError on unpickling
        data = pickle.loads(str(message.data))
    # could potentially throw a whole lot of different exceptions
    except:
        logger.error("Could not process message with id={0}: {1}".format(
            message_id, sys.exc_info()[0]))
        return (None, None)

    return (data, message)


def update_recency(object_type, object_id):
    """Creates one of those AnalyticsRecency things in the database."""
    recency, recency_created = AnalyticsRecency.objects.get_or_create(
        content_type=object_type,
        object_id=object_id
    )

    if not recency_created:
        recency.save()


def correct_date(row, logger):
    """Convert a string date e.g. 20130718 to a datetime object.

    # we do this here and not in fetching because celery can't
    # serialize certain things (e.g. datetime objects)

    """
    try:
        # <datetime>
        # convert string to a date, format the date, add a time zone
        row['date'] = datetime.strptime(row['date'], "%Y%m%d")\
                              .replace(tzinfo=utc)

    except (IndexError, ValueError):
        logger.warning("Date is unrecognized: %s", row['date'])

    return row


def create_parent_data(data):
    """
    For all subcategories, need to create additional rows for 'parent'
    category
    """
    def get_ir_campaign_by_pk(list_of_ir_campaigns, pk):
        """you have a list of ir campaigns already in memory.
        this can be fancier with list comprehension and whatnot, but that's
        what got us last time.
        """
        for ir_campaign in list_of_ir_campaigns:
            if ir_campaign.pk == pk:
                return ir_campaign
        return None

    missing_data = []
    campaign_ids = list(set([row.get('campaign_id') for row in data]))  # unique
    logger.info('Going to fetch {0} IntentRankCampaigns.'.format(
        len(campaign_ids)))

    # do a single fetch. we won't hit the memory limit any time soon;
    # worry about the SQLite "number of variables" limit for devs
    ir_campaigns = IntentRankCampaign.objects\
        .prefetch_related('campaigns')\
        .filter(pk__in=campaign_ids)

    logger.info('Fetched {0} IntentRankCampaigns.'.format(
        len(ir_campaigns)))

    for row in data:
        category_id = row.get('campaign_id')
        try:
            # get it from memory
            ir = get_ir_campaign_by_pk(ir_campaigns, category_id)

            # Since it's a M2M rel'n, even though we never associate
            # categories with other stores, we need to look through all of
            # the related campaigns and pick the *only* result

            parent_category = ir.campaigns.all()[0].default_intentrank_id
        except (IntentRankCampaign.DoesNotExist, AttributeError, IndexError):
            continue

        if int(category_id) == parent_category:
            continue

        new_row = deepcopy(row)
        new_row['campaign_id'] = parent_category
        missing_data.append(new_row)

    logger.info('{0} rows of missing data generated'.format(len(missing_data)))

    return missing_data


class Categories:
    """
    Caches analytics categories internally while providing useful shortcuts.
    Available keys per category slug:
        - instance: model instance
        - metric: function, takes metric slug and returns metric instance
                  if metric does not exist, throws an exception

    TODO: we have a categories cache and not a metrics cache?
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
    """Erases cached analytics and recency data, starts update process.
    To re-analyze existing data points in the database, consider using
    aggregate_saved_metrics instead.

    To use either: (http://stackoverflow.com/a/12900126)

    (venv)$ python manage.py shell
    > from apps.analytics.tasks import redo_analytics
    > redo_analytics.apply()
    or
    > from apps.analytics.tasks import aggregate_saved_metrics
    > aggregate_saved_metrics.apply()

    """
    logger.info("Redoing analytics")

    KVStore.objects.all().delete()
    AnalyticsRecency.objects.all().delete()

    logger.info("Removed old analytics data")

    restart_analytics.delay()  # === .run()


@task()
def restart_analytics():
    """Starts update process.

    To delete the database beforehand, use redo_analytics.
    """
    logger.info("Restarting analytics")

    # chord: parallel processing
    # disabled because it might not work
    task_chain = chain(group(fetch_awareness_data.subtask(),
                             fetch_event_data.subtask()),
                       group(process_awareness_data.subtask(),
                             process_event_data.subtask()),
                       aggregate_saved_metrics.subtask())

    # chain
    task_chain = chain(fetch_awareness_data.subtask(),
                       process_awareness_data.subtask(),
                       fetch_event_data.subtask(),
                       process_event_data.subtask(),
                       aggregate_saved_metrics.subtask())

    task_chain.delay()  # === .run()


@task()
def fetch_awareness_data(*args):
    """obtains data from google analytics via the GA API."""
    logger.info("Updating awareness analytics data")

    query = {
        'metrics': ['visitors', 'pageviews'],
        'dimensions': ['date', 'customVarValue1', 'customVarValue2',
            'socialNetwork', 'city', 'region'],
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
            location = u""
            try:
                if get_column_value(query, row, 'city') != "(not set)":
                    location = get_column_value(query, row, 'city').encode('utf-8', 'ignore')

                if get_column_value(query, row, 'region') != "(not set)" and \
                   get_column_value(query, row, 'region') not in location:
                    location = "{0}, {1}".format(
                        location, get_column_value(query, row, 'region').encode('utf-8', 'ignore'))
            except UnicodeDecodeError:  # happens with region names
                pass  # (location = location)


            row_data = {
                'date': get_column_value(query, row, 'date'),
                'store_id': get_column_value(query, row, 'customVarValue1'),
                'campaign_id': get_column_value(query, row, 'customVarValue2'),
                'visitors': get_column_value(query, row, 'visitors'),
                'pageviews': get_column_value(query, row, 'pageviews'),
                'socialNetwork': get_column_value(query, row, 'socialNetwork'),
                'location': location
            }

            # get a list of booleans for each row value
            all_present = all([row_data[key] is not None for key in row_data])

            if not all_present:
                logger.warning(
                    "GA row data is missing attributes: {0}".format(row_data))
                continue

            fetched_rows.append(row_data)

    # message could be larger than 64kb. As a quick way of circumventing the limitation,
    # use "shared memory" approach to message passing
    message = SharedStorage(data=pickle.dumps(fetched_rows))
    message.save()
    logger.info("dumped {0} rows into shared storage".format(len(fetched_rows)))

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
        'dimensions': ['eventCategory', 'eventAction', 'eventLabel',
            'socialNetwork', 'date', 'city', 'region'],
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
            category = get_column_value(query, row, 'eventCategory')
            action = get_column_value(query, row, 'eventAction')

            row_data = {
                'label':            get_column_value(query, row, 'eventLabel'),
                'date':             get_column_value(query, row, 'date'),
                'socialNetwork':    get_column_value(query, row, 'socialNetwork'),

                'store_id':         get_by_key(category, "storeid"),
                'campaign_id':      get_by_key(category, "campaignid"),
                'referrer':         get_by_key(category, "referrer"),
                'domain':           get_by_key(category, "domain"),

                'action_type':      get_by_key(action, "actionType"),
                'action_subtype':   get_by_key(action, "actionSubtype"),
                'action_scope':     get_by_key(action, "actionScope"),
                'network':          get_by_key(action, "network")
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
    logger.info("dumped {0} categories into shared storage".format(
        len(analytics_categories)))

    # pass ID of the message to the processing task
    return message.id


@task()
@transaction.commit_manually
def process_awareness_data(message_id):
    """Processes fetched awareness data, row by row"""
    store_type = ContentType.objects.get_for_model(Store)
    campaign_type = ContentType.objects.get_for_model(Campaign)

    data, message = get_message_by_id(message_id)
    if not data:
        logger.error("Message {0} not found!".format(message_id))
        return

    updated_stores = []  # recency data will be populated for those updated
    updated_campaigns = []  # (which are usually all stores and campaigns)

    categories = Categories()

    columns_to_save = [{'key': 'awareness-visitors',
                        'value': 'visitors',
                        'meta': 'socialNetwork'},
                       {'key': 'awareness-pageviews',
                        'value': 'pageviews',
                        'meta': 'socialNetwork'},
                       {'key': 'awareness-location',
                        'value': 'visitors',
                        'meta': 'location'}]

    logger.info('#{0}: Creating missing data'.format(message_id))
    missing_data = create_parent_data(data)
    data.extend(missing_data)

    len_data = len(data)
    i = 0
    for row in data:
        i = i + 1  # informative counter
        if i % 50 == 0:
            transaction.commit()  # avoid exceeding the transaction size
            logger.info('#{0}: processing row {1}/{2}'.format(
                message_id, i, len_data))

        row = correct_date(row, logger)
        for column in columns_to_save:
            save_data_pair(store_type, campaign_type,
                           categories.get("awareness"), row, column)

        if not row['store_id'] in updated_stores:
            updated_stores.append(row['store_id'])
        if not row['campaign_id'] in updated_campaigns:
            updated_campaigns.append(row['campaign_id'])

    # Update analytics recency data for all affected stores and campaigns
    for store_id in updated_stores:
        update_recency(store_type, store_id)

    for campaign_id in updated_campaigns:
        update_recency(campaign_type, campaign_id)

    # we can safely delete the passed message at this point
    message.delete()

    transaction.commit()  # consolidate

    return None

@task()
@transaction.commit_manually
def process_event_data(message_id):
    """Processes fetched event data, row by row, saves key/value
    analytics pairs for associated store and campaign"""
    store_type = ContentType.objects.get_for_model(Store)
    campaign_type = ContentType.objects.get_for_model(Campaign)

    data, message = get_message_by_id(message_id)
    if not data:
        logger.error("Message {0} not found!".format(message_id))
        return

    updated_stores = []
    updated_campaigns = []

    logger.info('#{0}: Creating category cache'.format(message_id))
    categories = Categories()

    # handle sharing data
    category_names = data.keys()
    i = 0
    len_data = sum([len(data[slug]) for slug in category_names])
    logger.info('#{0}: Going to process {1} rows.'.format(message_id, len_data))

    for category_slug in category_names:
        logger.info('#{0}: Creating missing data'.format(message_id))
        missing_data = create_parent_data(data[category_slug])
        data[category_slug].extend(missing_data)

        for row in data[category_slug]:
            i = i + 1  # informative counter
            if i % 50 == 0:
                transaction.commit()  # avoid exceeding the transaction size
                logger.info('#{0}: processing row {1}/{2}'.format(
                    message_id, i, len_data))

            # with each pass, we're saving a pair of KVStore objects
            # one for the specific campaign, and one for the store
            # to which the campaign belongs

            # we do this here and not in fetching because celery can't
            # serialize certain things (e.g. datetime objects)
            row = correct_date(row, logger)

            column = {
                'key': '{0}-{1}'.format(
                    row['action_type'], row['action_subtype']),
                'value': 'count'
            }
            if row['action_type'] == "share":
                column['meta'] = 'network'
            else:
                column['meta'] = 'action_scope'

            # save main event
            save_data_pair(store_type, campaign_type,
                           categories.get(category_slug), row, column)

            # save event's source network information
            column = {
                'key': '{0}-{1}-{2}'.format(
                    row['action_type'], row['action_subtype'], 'source'),
                'value': 'count',
                'meta': 'socialNetwork'
            }
            save_data_pair(store_type, campaign_type,
                           categories.get(category_slug), row, column)

            if not row['store_id'] in updated_stores:
                updated_stores.append(row['store_id'])
            if not row['campaign_id'] in updated_campaigns:
                updated_campaigns.append(row['campaign_id'])

        transaction.commit()  # save for each category

    # Update analytics recency data for all affected stores and campaigns
    logger.info('#{0}: Updating store recency'.format(message_id))
    for store_id in updated_stores:
        update_recency(store_type, store_id)

    logger.info('#{0}: Updating campaign recency'.format(message_id))
    for campaign_id in updated_campaigns:
        update_recency(campaign_type, campaign_id)

    # we can safely delete the passed message at this point
    message.delete()
    logger.info('#{0}: Deleted message'.format(message_id))

    transaction.commit()  # consolidate
    logger.info('#{0}: Transaction successful!'.format(message_id))

    return None

@task()
@transaction.commit_manually
def aggregate_saved_metrics(*args):
    """Calculates "meta" metrics, which are combined out of "raw" saved data"""

    # This function generates meta metrics.
    # Remove all the existing meta metric data
    KVStore.objects.filter(meta="meta_metric").delete()

    def adder(adder_obj, datum, metric_obj, content_type, object_id, key,
              timestamp, meta):
        """attempts to cache all meta KVStore writes until the end.

        Function signature is the same as KVStore lookups.

        @param adder_objd: mutable dict or defaultdict(list)
        @param object_id: either a store_id or a campaign_id
        @param content_type: whether the object_id was of a store or a campaign
        """

        # did you know that any hashable value can be a dict key?
        temp_key = (content_type, object_id, key, timestamp, meta)

        if 'aggregator' in metric_obj:
            # allows for custom aggregation: average, etc
            custom_aggregation_func = metric_obj['aggregator']
            adder_obj[temp_key] = custom_aggregation_func(datum.value)
        else:
            try:
                adder_obj[temp_key] += datum.value
            except KeyError:
                adder_obj[temp_key] = datum.value

    def process_category(obj):
        """
        Adds a new KV, using it as a per-day summation for KV data
        defined by passed in Q filters
        """
        category_data = KVStore.objects.filter(obj['q_filter'])

        for metric_obj in obj['metrics']:  # => [{slug, key, q_filter}]
            logger.info('processing metric "{0}"'.format(metric_obj['slug']))
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

            logger.info('{0} "{1}" objects to aggregate'.format(
                len(data), metric_obj['slug']))

            adder_cache = {}  # reset per key
            i = 0
            len_data = len(data)
            for datum in data:
                i = i + 1  # informative counter
                if i % 50 == 0:
                    logger.info('{0}: aggregating row {1}/{2}'.format(
                        metric_obj['slug'], i, len_data))

                # add all values before calling db
                adder(adder_cache, datum=datum, metric_obj=metric_obj,
                      content_type=datum.content_type,
                      object_id=datum.object_id, key=metric_obj['key'],
                      timestamp=datum.timestamp, meta="meta_metric")

            # adder cache is now full of already-aggregated keys and values
            # key format: (content_type, object_id, key, timestamp, meta)
            i = 0
            len_data = len(adder_cache)  # it's a dict
            for aggregated_metric in adder_cache:
                i = i + 1  # informative counter
                if i % 50 == 0:
                    transaction.commit()  # avoid exceeding the transaction size
                    logger.info('{0}: committing row {1}/{2}'.format(
                        metric_obj['slug'], i, len_data))
                kwargs = {'content_type': aggregated_metric[0],
                          'object_id': aggregated_metric[1],
                          'key': aggregated_metric[2],
                          'timestamp': aggregated_metric[3],  # per-day
                          'meta': aggregated_metric[4]}
                try:
                    # meta-kv already present, increment
                    kv = KVStore.objects.get(**kwargs)
                except KVStore.DoesNotExist:  # need to create the meta-kv
                    kv = KVStore(**kwargs)

                try:
                    kv.value += adder_cache[aggregated_metric]
                except (KeyError, ValueError):
                    # neither should happen, but we really don't want
                    # SQS to redo this task because of an exception.
                    kv.value = adder_cache[aggregated_metric]
                kv.save()


                metric.data.add(kv)
            transaction.commit()  # save for each datum
        return None

    # this list defines how the data for "meta-metrics" is to be calculated
    # list is a series of categories to process

    # each category contains a lookup query to define a common dataset
    # for the metrics to work with

    # it also defines a list of metrics to process
    # each metric defines a further lookup query
    # to further narrow down the  category data

    # process_category function then does daily sums of said data

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
                    'q_filter': Q(key__in=['inpage-hover', 'inpage-openpopup']),
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
                # Total Shares
                {
                    'slug': 'total-shares',
                    'key': 'share-total',
                    'q_filter': Q(key__in=['share-clicked', 'share-liked'])
                },
            ]
        },

        # Awareness
        {
            'q_filter': Q(key__startswith="awareness-"),

            'metrics': [
                # Total Visitors
                {
                    'slug': 'awareness-visitors',
                    'key': 'awareness-visitors-total',
                    'q_filter': Q(key='awareness-visitors')
                },

                # Total Pageviews
                {
                    'slug': 'awareness-pageviews',
                    'key': 'awareness-pageviews-total',
                    'q_filter': Q(key='awareness-pageviews')
                }
            ]
        }
    ]

    for category in to_process:
        process_category(category)

    transaction.commit()  # consolidate