import datetime

from celery import task, subtask
from oauth2client.client import SignedJwtAssertionCredentials

from django.contrib.contenttypes.models import ContentType

from apps.analytics.storage_backends import GoogleAnalyticsBackend
from apps.analytics.models import AnalyticsRecency, Category, Metric, KVStore
from apps.assets.models import Store
from apps.pinpoint.models import Campaign


def get_oldest_analytics_date():
    """Figure out earliest date for which we're missing analytics data"""

    oldest_analytics_data = datetime.datetime.now().date()

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

            oldest_analytics_data = datetime.date(2012, 9, 1)

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

    AnalyticsData.objects.all().delete()
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
    def get_by_key(string, key):
        """Gets a variable stored within a GA column by its key

        Column format: var1=value|var2=value
        """

        ls = string.split("|")
        try:
            return [s for s in ls if key in s][0].split("=")[1]
        except IndexError:
            return None

    def row_getter(row):
        """Get a data column from provided row"""

        def get(key):
            """Column is looked up by an index from dimensions settings"""

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
    start_from_date = datetime.date(2012, 9, 1)

    logger.info("We need to fetch analytics data from GA starting from %s",
        start_from_date)

    raw_results = ga.results_iterator(
        # start date
        start_from_date,

        # end date
        datetime.datetime.now().date(),

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

        if not data_page.get('rows', []):
            logger.info("No rows available.")
            continue

        rows = data_page.get('rows')

        for row in rows:
            row_data = {}
            getter = row_getter(row)

            category = getter('eventCategory')
            action = getter('eventAction')

            row_data['label'] = getter('eventLabel')
            row_data['date'] = getter('date')

            row_data['store_id'] = get_by_key(category, "storeid")
            row_data['campaign_id'] = get_by_key(category, "campaignid")
            row_data['referrer'] = get_by_key(category, "referrer")
            row_data['domain'] = get_by_key(category, "domain")

            row_data['action_type'] = get_by_key(action, "actionType")
            row_data['action_subtype'] = get_by_key(action, "actionSubtype")
            row_data['action_scope'] = get_by_key(action, "actionScope")
            row_data['network'] = get_by_key(action, "network")

            # uniqueEvents is the last item in the list
            try:
                row_data['count'] = int(row[len(row) - 1])

            except ValueError:
                logger.warning(
                    "GA row data isn't what we're expecting: count=%s",
                    row[row.length - 1])
                continue

            # check that all variables in row_data are present
            all_present = reduce(
                # reduce list of booleans into one value
                lambda total, check: total and check,

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

            elif row_data['action_type'] == 'sharing':
                analytics_categories['sharing'].append(row_data)

    return subtask(save_category_data, data=analytics_categories).delay()

@task()
def save_category_data(data):
    """Processes individual data row, saves key/value
    analytics pairs for associated store and campaign"""

    logger = save_category_data.get_logger()

    try:
        store = Store.objects.get(id=row['store_id'])

    except Store.DoesNotExist:
        logger.warning("Store with id %s does not exist. Skipping row",
            row['store_id'])
        return

    try:
        campaign = Campaign.objects.get(id=row['campaign_id'])

    except Campaign.DoesNotExist:
        logger.warning("Campaign with id %s does not exist. Skipping row",
            row['campaign_id'])
        return

    store_type = ContentType.objects.get_for_model(Store)
    campaign_type = ContentType.objects.get_for_model(Campaign)

    section, created = Section.objects.get_or_create(slug="main")
    categories = {
        'engagement': section.categories.filter(slug='engagement'),
        'sharing': section.categories.filter(slug='sharing')
    }

    updated_stores = []
    updated_campaigns = []

    # handle sharing data
    for row in data['sharing']:
        # we do this here and not in "pre processing" because celery can't
        # serialize certain things (e.g. datetime objects)
        row = preprocess_row(row)

        # total sharing
        # total sharing per network
        # sharing per scope
        # sharing per scope per network
        # share vs click

        if row['store_id'] not in updated_stores:
            updated_stores.append(row['store_id'])

        if row['campaign_id'] not in updated_campaigns:
            updated_campaigns.append(row['campaign_id'])

    # handle engagement data
    for row in data['engagement']:
        row = preprocess_row(row)

        # total interactions
        # product interactions
        # interactions per scope
        # clickthrough
        # open popup
        # buy now
        # share

        if row['store_id'] not in updated_stores:
            updated_stores.append(row['store_id'])

        if row['campaign_id'] not in updated_campaigns:
            updated_campaigns.append(row['campaign_id'])

    # Update analytics recency data for all affected stores and campaigns
    for updated_store_id in updated_stores:
        store_recency = AnalyticsRecency.objects.get_or_create(
            content_type=store_type,
            object_id=updated_store_id
        )

        if not store_recency[1]:
            store_recency.save()

    for updated_campaign_id in updated_campaigns:
        campaign_recency = AnalyticsRecency.objects.get_or_create(
            content_type=campaign_type,
            object_id=updated_campaign_id
        )

        if not campaign_recency[1]:
            campaign_recency.save()

def preprocess_row(row, logger):
    try:
        row['date'] = datetime.datetime(
            int(row['date'][:4]), int(row['date'][4:6]), int(row['date'][-2:]))

    except (IndexError, ValueError):
        logger.warning("Date is unrecognized: %s", row['date'])

    return row
