import datetime

from celery import task, subtask
from oauth2client.client import SignedJwtAssertionCredentials

from django.contrib.contenttypes.models import ContentType

from apps.analytics.storage_backends import GoogleAnalyticsBackend
from apps.analytics.models import AnalyticsData, AnalyticsRecency
from apps.assets.models import Store, Product


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
    logger = update_pinpoint_analytics.get_logger()
    logger.info("Updating analytics data")

    # define what we're requesting from Google Analytics
    metrics = ['uniqueEvents']
    dimensions = ['eventCategory', 'eventAction', 'eventLabel', 'date']
    sort = ['date']

    # initialize GA backend
    ga = GoogleAnalyticsBackend()

    # figure out data range that we'd need to fetch from GA
    oldest_analytics_data = datetime.datetime.now().date()

    # iterate through our stores and find the most out of sync
    stores = Store.objects.all()

    for store in stores:
        store_type = ContentType.objects.get_for_model(Store)

        try:
            analytics_recency = AnalyticsRecency.objects.get(
                content_type=store_type, object_id=store.id)

        except AnalyticsRecency.DoesNotExist:
            # no pinpoint analytics data was fetched for this store
            # get everything, use the prior-to-launch date so that
            # we're sure everything is in scope

            oldest_analytics_data = datetime.date(2012, 9, 1)

            # we're done checking for dates at this point
            break

        else:
            # have recency data, see if it's older than oldest recency
            if analytics_recency.last_fetched < oldest_analytics_data:
                oldest_analytics_data = analytics_recency.last_fetched.date()

    logger.info("We need to fetch analytics data from GA starting from %s",
        oldest_analytics_data)

    # @TODO: "coercing" to string functionality should be in the backend
    raw_results = ga.results_iterator(
        "%s" % oldest_analytics_data,
        "%s" % datetime.datetime.now().date(),  # end date
        metrics,
        dimensions=dimensions,
        sort=sort,
    )

    if not raw_results:
        logger.info("Couldn't get analytics raw data. Nothing to do.")
        return

    for data_page in raw_results:
        logger.info("Processing results page %s", data_page)

        if not data_page.get('rows', []):
            logger.info("No rows available.")
            continue

    #     data_parser.map_rows(data_page.get('rows'))

    # for store in stores:
    #     data_parser.reduce(store)

@task()
def analytics_periodic():
    """Dynamically loads storage backends of installed analytics modules
    and tells storage backend to start the appropriate cron job.

    First load the appropriate storage backend.
    Use it to initialize analyitcs instance.
    """

    for module in INSTALLED_ANALYTICS.keys():

        StorageBackend = getattr(storage_backends,
            INSTALLED_ANALYTICS[module]["storage_backend"]
        )

        storage_backend = StorageBackend()

        _analytics_processes = __import__(
            "apps.analytics.%s.tasks" % module,
            globals(), locals(), [ANALYTICS_CLASS_NAME], -1
        )

        AnalyticsPeriodic = getattr(_analytics_processes, ANALYTICS_CLASS_NAME)

        analytics_instance = AnalyticsPeriodic(storage_backend)
        analytics_instance.start()
