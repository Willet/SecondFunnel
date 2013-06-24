"""Various storage backends for analytics events.

Currently only Google Analytics is supported.
"""

import httplib2
import logging

from apiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials
from celery.utils.log import get_task_logger

from django.conf import settings

logger = get_task_logger(__name__)


def join_params(params, join_with=","):
    if not params:
        return None

    return join_with.join(map(lambda p: "ga:%s" % p, params))


class GoogleAnalyticsBackend:
    """Mediates access to Google Analytics APIs"""

    def __init__(self):
        with open(settings.GOOGLE_API_PRIVATE_KEY, 'rb') as private_key:
            key = private_key.read()

        credentials = SignedJwtAssertionCredentials(
            settings.GOOGLE_SERVICE_ACCOUNT,
            key,
            scope='https://www.googleapis.com/auth/analytics.readonly')

        http = httplib2.Http()
        http = credentials.authorize(http)

        self.service = build('analytics', 'v3', http=http)

    def create_query(self, start_date, end_date, metrics, dimensions=None,
                     sort=None, filters=None, start_index="1",
                     max_results='10000'):
        if filters is not None:
            filters = ["{0}{1}".format(f[0], f[1]) for f in filters]

        """
        logging.error([self, start_date, end_date, metrics, dimensions,
                     sort, filters, start_index,
                     max_results])
        [<apps.analytics.storage_backends.GoogleAnalyticsBackend instance at 0x47c13b0>,
         '2013-01-01',
         '2013-06-24',
         ['visitors', 'pageviews'],
         ['date', 'customVarValue1', 'customVarValue2', 'socialNetwork', 'city', 'region'],
         ['date'],
         ['pagePath!@pinpoint', 'hostname!@127', 'hostname!@localhost', 'hostname!@elasticbeanstalk', 'hostname!@0.0.0.0'],
         u'https://www.googleapis.com/analytics/v3/data/ga?ids=ga:67271131&dimensions=ga:date,ga:customVarValue1,ga:customVarValue2,ga:socialNetwork,ga:city,ga:region&metrics=ga:visitors,ga:pageviews&sort=ga:date&filters=ga:pagePath!@pinpoint;ga:hostname!@127;ga:hostname!@localhost;ga:hostname!@elasticbeanstalk;ga:hostname!@0.0.0.0&start-date=2013-01-01&end-date=2013-06-24&start-index=10001&max-results=10000',
         '10000']
        """
        api_query = self.service.data().ga().get(
            ids="ga:%s" % settings.GOOGLE_ANALYTICS_PROFILE,
            start_date=start_date,
            end_date=end_date,
            metrics=join_params(metrics),
            dimensions=join_params(dimensions),
            sort=join_params(sort),
            filters=join_params(filters, join_with=";"),
            start_index=start_index,
            max_results=max_results
        )

        return api_query

    def get_results(self, api_query):
        try:
            results = api_query.execute()
            return results

        except TypeError, error:
            logging.error(
                'There was an error constructing Google Analytics query : %s',
                error)

            return None

        except Exception, error:
            logging.error(
                'There was a Google Analytics Core API error : %s', error)
            return None

    def results_iterator(self, start_date, end_date, metrics, dimensions=None,
                         sort=None, filters=None, max_results='10000',
                         start_index="1"):
        """
        Creates a generator over google analytics results data
        which is likely spanning multiple pages
        """

        # coerce dates into strings for Google Analytics
        start_date = str(start_date)
        end_date = str(end_date)

        # these filter out internal requests to pages
        default_filters = [
            ('pagePath', '!@pinpoint'),
            ('hostname', '!@127'),
            ('hostname', '!@localhost'),
            ('hostname', '!@elasticbeanstalk'),
            ('hostname', '!@0.0.0.0')
        ]

        if not filters:
            filters = default_filters

        while True:
            next_query = self.create_query(
                start_date, end_date, metrics,
                dimensions=dimensions,
                sort=sort,
                filters=filters,
                start_index=start_index,
                max_results=max_results
            )
            results = self.get_results(next_query)
            yield results

            logging.error([int(start_index) + int(results.get('itemsPerPage')),
                                  int(results.get('totalResults'))])
            if results.get('itemsPerPage') and results.get('totalResults'):
                # start_index = results.get('nextLink')
                start_index = min(int(start_index) + int(results.get('itemsPerPage')),
                                  int(results.get('totalResults')))
            else:
                return