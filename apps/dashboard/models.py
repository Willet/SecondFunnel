from apiclient.discovery import build
from apiclient.errors import HttpError
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
import httplib2
import json
import requests
import jsonfield
from oauth2client.client import SignedJwtAssertionCredentials
import re
from string import capitalize
from django.utils.timezone import now


class Query(models.Model):
    # the name the query goes by
    identifier = models.CharField(max_length=128, help_text='The name of this query.')

    cached_response = jsonfield.JSONField(default={})

    timestamp = models.DateTimeField(auto_now=True,
                                     verbose_name="The last time a response was saved")

    def get_query(self, query_id, start_date, end_date):
        """
        Returns a query object for use by get_response (or other things)
        """
        raise NotImplementedError("This is an abstract method and must be overridden")

    def get_response(self, query_id, start_date, end_date):
        """
        Returns a JSON string with the data from an api query
        """
        raise NotImplementedError("This is an abstract method and must be overridden")

    def __unicode__(self):
        name = 'null'
        try:
            name = self.identifier
        except:
            print 'no identifier, please save the object'
        return name

    class Meta:
        abstract = True


class AnalyticsQuery(Query):
    metrics = models.CharField(max_length=512)
    dimensions = models.CharField(max_length=256)

    @staticmethod
    def get_end_date(date):
        if date < now():
            return 'today'
        return date.strftime('%Y-%m-%d')

    @staticmethod
    def get_start_date(date):
        if date > now():
            return 'today'
        return date.strftime('%Y-%m-%d')

    @staticmethod
    def build_analytics():
        """
        Builds and returns an Analytics service object authorized with the given service account
        Returns a service object
        """
        f = open(settings.SERVICE_ACCOUNT_PKCS12_FILE_PATH, 'rb')
        key = f.read()
        f.close()

        credentials = SignedJwtAssertionCredentials(settings.SERVICE_ACCOUNT_EMAIL,
                                                    key,
                                                    scope='https://www.googleapis.com/auth/analytics.readonly')
        http = httplib2.Http()
        http = credentials.authorize(http)

        return build('analytics', 'v3', http=http)

    def get_query(self, query_id, start_date, end_date, campaign='all'):
        """
        Gets the query object for this query with the given table id.
        Returns a analytics query object that has an execute method,
            calling analyticsQuery.get_query().execute() will return
            a response (in JSON)
        """
        service = AnalyticsQuery.build_analytics()
        data = service.data().ga().get(ids=query_id,
                                       start_date=self.get_start_date(start_date),
                                       end_date=self.get_end_date(end_date),
                                       metrics=self.metrics,
                                       dimensions=self.dimensions,
                                       output='dataTable',
                                       filter='')
        return data

    def get_response(self, query_id, start_date, end_date, campaign='all'):
        response = {'error': 'Failed to retrieve data'}
        try:
            response = self.get_query(query_id, start_date, end_date, campaign=campaign).execute()
        except HttpError as error:
            print "Querying Google Analytics failed with: ", error
            return response + self.cached_response

        if 'dataTable' in response:
            for header in response['dataTable']['cols']:
                header['label'] = header['label'].split(':')[1]
                # Complicated reg-ex:
                #   first group is all lower case,
                #   second is a single group capital/digit followed by more digits or lower case.
                #   ie. goal2Completions -> [(u'goal', u''), (u'', u'2'), (u'', u'Completions')]
                temp_title = re.findall(r'(^[a-z]*)|([\dA-Z]{1}[\da-z]*)', header['label'])
                # Then take the correct group, make it uppercase, and add them together to form
                #   the pretty human readable title for the dataTable columns
                # TODO : replace goal 2 etc with descriptive names
                title = ''
                for group in temp_title:
                    if group[0] == u'':
                        title += group[1] + ' '
                    else:
                        title += capitalize(group[0]) + ' '
                title = title.replace('Goal 1', 'Preview')
                title = title.replace('Goal 2', 'Buy Now')
                title = title.replace('Goal 3', 'Scroll')
                title = title.replace('Conversion', '')
                header['label'] = title
            for row in response['dataTable']['rows']:
                row['c'][0]['v'] = capitalize(row['c'][0]['v'])
        else:
            if 'rows' in response:
                for row in response['dataTable']['rows']:
                    row['c'][0]['v'] = capitalize(row['c'][0]['v'])
        if not 'error' in response:
            self.cached_response = json.dumps(response)
            self.save()
        return self.cached_response


class ClickmeterQuery(Query):
    """
    Currently only supports getting conversions and other data that takes similar parameters
    """
    endpoint = models.CharField(max_length=128)
    group_by = models.CharField(max_length=64)

    @staticmethod
    def get_end_date(date):
        return date.strftime('%Y%m%d')

    @staticmethod
    def get_start_date(date):
        return date.strftime('%Y%m%d')

    def get_query(self, query_id, start_date, end_date):
        """
        Do authentication and then prepare a request
        """
        url = 'http://apiv2.clickmeter.com' + self.endpoint.format(query_id)
        auth_header = {'X-Clickmeter-Authkey': settings.CLICKMETER_API_KEY}
        data = {'id': query_id,
                'timeframe': 'custom',
                'fromDate': self.get_start_date(start_date),
                'toDate': self.get_end_date(end_date),
                'groupBy': self.group_by}
        return {'url':  url, 'header': auth_header, 'payload': data}

    def get_response(self, query_id, start_date, end_date):
        query = self.get_query(query_id, start_date, end_date)
        response = {'error': 'Failed to retrieve data'}

        try:
            response = requests.get(query['url'], header=query['header'], params=query['payload'])
        except HttpError as error:
            print "Querying Clickmeter failed with: ", error
            return response + self.cached_response

        if not 'error' in response:
            self.cached_response = json.dumps(response)
            self.save()
        return self.cached_response


class Campaign(models.Model):
    title = models.CharField(max_length=128)
    google_id = models.CharField(max_length=128)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __unicode__(self):
        name = 'null'
        try:
            name = self.title
        except:
            print 'please save and give campaign a title'
        return name


class DashBoard(models.Model):
    """
    The analytics information for a given site.
    Each metric is a JSON file containing the response from a
    query to the Google Analytics for the given site with respect to certain dimensions
    """
    # human name for the site that these statistics correspond to
    site_name = models.CharField(max_length=128)
    # prepend with 'ga:' this is the table id that GA uses to refer to the site
    table_id = models.IntegerField(help_text="The number that refers to this customers analytics data")

    def __unicode__(self):
        name = 'null'
        try:
            name = self.site_name
        except:
            print 'no site, please save object with a site'
        return name


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    dashboards = models.ManyToManyField(DashBoard)

    def __unicode__(self):
        username = "null"
        try:
            username = self.user.username
        except:
            print 'self.user.username caused an exception. Is there a user?'
        return username
