"""Various storage backends for analytics events.

Currently only Google Analytics is supported.
"""

import httplib2
import logging

from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials

from django.conf import settings


class GoogleAnalyticsBackend:
    """Mediates access to Google Analytics APIs"""

    def __init__(self):
        # TODO: REDO THIS! Use SWK Signed object
        credentials = AppAssertionCredentials(
            scope='https://www.googleapis.com/auth/analytics.readonly')

        http = credentials.authorize(httplib2.Http())
        self.service = build('analytics', 'v3', http=http)

    def get_service(self):
        return self.service

    def get_profile_id(self):
        return settings.GOOGLE_ANALYTICS_PROFILE

    def join_params(self, params):
        if not params:
            return None

        return ",".join(map(lambda p: "ga:%s" % p, params))

    def create_query(self, start_date, end_date, metrics, dimensions=None, sort=None, start_index="1", max_results='10000'):
        api_query = self.service.data().ga().get(
            ids="ga:%s" % self.get_profile_id(),
            start_date=start_date,
            end_date=end_date,
            metrics=self.join_params(metrics),
            dimensions=self.join_params(dimensions),
            sort=self.join_params(sort),
            start_index=start_index,
            max_results=max_results,
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

    def results_iterator(self, start_date, end_date, metrics, dimensions=None, sort=None, max_results='10000', start_index="1"):
        """
        Creates a generator over google analytics results data
        which is likely spanning multiple pages
        """

        while True:
            next_query = self.create_query(
                start_date, end_date, metrics,
                dimensions=dimensions, sort=sort, start_index=start_index,
                max_results=max_results
            )
            results = self.get_results(next_query)
            yield results

            if not results.get('nextLink'):
                return
            else:
                start_index = results.get('nextLink')
