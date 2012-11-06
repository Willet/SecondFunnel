"""
Periodic tasks to generate user-facing analyitcs data for PinPoint.
"""
import logging
import datetime

from django.contrib.contenttypes.models import ContentType

from apps.analytics.models import AnalyticsData, AnalyticsRecency
from apps.assets.models import Store, Campaign



class AnalyticsPeriodic:
    """
    Fetches data from Google Analytics, calculates our key metrics
    and saves them.
    """
    def __init__(self, ga_backend):
        self.backend = ga_backend
        self.service = ga_backend.get_service()
        self.recencies = {}

    def start(self):
        logging.info("Starting to gather pinpoint analytics data")

        # figure out data range that we'd need to fetch from GA
        oldest_analytics_data = datetime.datetime.now().date()

        # iterate through our stores and fine the most out of sync
        stores = Store.objects.all()
        campaigns = Campaign.objects.all()

        for store in stores:
            store_type = ContentType.objects.get_for_model(Store)

            try:
                analytics_recency = AnalyticsRecency.objects.get(
                    content_type=store_type, object_id=store.id)

            except AnalyticsRecency.KeyError:
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

                self.recencies[store] = analytics_recency

        self.parse_analytics_data(oldest_analytics_data, stores=stores, campaigns=campaigns)

    def parse_analytics_data(self, start_date, stores, campaigns):
        """start_date must be instance of datetime.date"""

        # define what we're requesting from Google Analytics
        metrics = ['uniqueEvents']
        dimensions = ['eventCategory', 'eventAction', 'eventLabel', 'date']
        sort = ['date']

        # @TODO: "coercing" to string functionality should be in the backend
        raw_results = self.backend.results_iterator(
            "%s" % start_date,
            "%s" % datetime.datetime.now().date(),  # end date
            metrics,
            dimensions=dimensions,
            sort=sort,
        )

        if not raw_results:
            logging.info("Couldn't get analytics raw data. Nothing to do.")
            return

        data_parser = DataParser(self, dimensions)

        for data_page in raw_results:
            logging.info("Processing results page %s", data_page)

            if not data_page.get('rows', []):
                logging.info("No rows available.")
                continue

            data_parser.map_rows(data_page.get('rows'))

        for store in stores:
            data_parser.reduce(store)



class DataParser:
    def __init__(self, analytics_periodic, dimensions):
        self.results = {
            'campaigns': {},
            'stores': {}
        }

        self.dimensions = dimensions
        self.cron = analytics_periodic

    def reduce(self, store):
        try:
            rows = self.results[app.uuid]
        except KeyError:
            logging.warning(
                "Requested %s, but it's missing from mapped data: %s",
                app.uuid, self.results)
        else:
            per_day_data = {}

            for row in rows:
                datum = {
                    'cohort_id': row['cohort_id'],
                    'referral': row['referral'],
                    'system': row['system'],
                    'action': row['action'],
                    'count': row['count'],
                }
                if not row['product_id'] in per_day_data:
                    per_day_data[row['product_id']] = {}

                if not row['date'] in per_day_data[row['product_id']]:
                    per_day_data[row['product_id']][row['date']] = [datum]
                else:
                    per_day_data[row['product_id']][row['date']].append(datum)

            product = None
            # save daily stats
            for product_id in per_day_data.keys():
                if product_id:
                    product = Product.get(product_id)

                for date in per_day_data[product_id].keys():
                    # end of the day
                    end_date = date + datetime.timedelta(days=1) - datetime.timedelta(minutes=1)

                    for event in per_day_data[product_id][date]:
                        cohort = None
                        if 'cohort_id' in event and event['cohort_id']:
                            cohort = ReEngageCohortID.get(event['cohort_id'])

                        analytics_data = AnalyticsResultsStorage(
                            analytics_type=self.cron.leadspeaker_analytics,
                            application=app,
                            product=product,
                            cohort_id=cohort,
                            start_datetime=date,
                            end_datetime=end_date,
                            referral=event['referral'],
                            action=event['action'],
                            value=event['count'],
                            uuid=generate_uuid(16)
                        )
                        analytics_data.put()
                        logging.info("Saved data for app=%s, product=%s, date=%s, event=%s",
                                     app.uuid, product.uuid, date, event)

            recency_query = db.Query(AnalyticsResultsRecency).filter(
                'analytics_type =', self.cron.leadspeaker_analytics).filter(
                'application =', app)

            if recency_query.count() > 0:
                recency = recency_query.get()
                recency.timestamp = datetime.datetime.now()
            else:
                recency = AnalyticsResultsRecency(application=app,
                    analytics_type=self.cron.leadspeaker_analytics,
                    uuid=generate_uuid(16))
                recency.put()

    def map_rows(self, rows):
        """
        Go through rows, parse out data, and store into
        a results dictionary under the object's id
        """

        # helper methods
        def get_by_key(string, key):
            ls = string.split("|")
            try:
                return [s for s in ls if key in s][0].split("=")[1]
            except:
                return None

        def row_getter(row):
            def get(key):
                return row[self.dimensions.index(key)]
            return get

        for row in rows:
            getter = row_getter(row)

            category = getter('eventCategory')
            action = getter('eventAction')
            label = getter('eventLabel')

            store_id = get_by_key(category, "storeid")
            campaign_id = get_by_key(category, "campaignid")
            referrer = get_by_key(category, "referrer")
            domain = get_by_key(category, "domain")

            action_type = get_by_key(action, "actionType")
            action_subtype = get_by_key(action, "actionSubtype")
            action_scope = get_by_key(action, "actionScope")
            network = get_by_key(action, "network")

            # data isn't what we're expecting, don't proceed
            if not (store_id and campaign_id and referrer \
                    and domain and action_type and action_subtype \
                    and action_scope and network):

                logging.warning(
                    "GA row data isn't what we're expecting, missing attributes, category=%s, action=%s",
                    category, action)
                continue

            # uniqueEvents is the last item in the list
            try:
                count = int(row[len(row) - 1])

            except ValueError:
                logging.warning(
                    "GA row data isn't what we're expecting: count=%s",
                    row[row.length - 1])
                continue

            date = getter('date')
            try:
                date = datetime.datetime(
                    int(date[:4]), int(date[4:6]), int(date[-2:]))
            except (IndexError, ValueError):
                logging.warning(
                    "GA row data isn't what we're expecting: date=%s", date)
                continue

            # row template
            mapped_row = {
                "visits": 0,
                "interactions": {
                    "total": 0,
                    "clickthrough": 0,
                    "open_popup": 0,
                    "shares": {
                        "featured": 0,
                        "popup": 0
                    }
                }
            }
            if not store_id in self.results['stores']:
                self.results['stores'][store_id] = {}

            if not campaign_id in self.results['campaigns']:
                self.results['campaigns'][campaign_id] = {}




            if action_scope == "popup":
                maped_row['interactions']['shares']

            mapped_row = {
                "product_id": product_id,
                "cohort_id": cohort_id,
                "action": action,
                "system": from_system,
                "referral": referral,
                "count": count,
                "date": date
            }

            if app_uuid in self.results:
                self.results[app_uuid].append(mapped_row)
            else:
                self.results[app_uuid] = [mapped_row]
