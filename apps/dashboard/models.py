from datetime import timedelta
import httplib2
import requests
import json
import jsonfield
import re

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import SignedJwtAssertionCredentials

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

from model_utils.managers import InheritanceManager
from string import capitalize
from django.utils.timezone import now


class Query(models.Model):
    # the name the query goes by
    identifier = models.CharField(max_length=128, help_text='The name of this query.', unique=True)
    cached_response = jsonfield.JSONField(default={}, blank=True)
    is_today = models.BooleanField(default=False)
    # TODO add the code that uses this in queries
    timestamp = models.DateTimeField(auto_now=True,
                                     verbose_name="The last time a response was saved")

    # The manager that makes it so that queries will return children if possible
    objects = InheritanceManager()

    def get_query(self, page):
        """
        Returns a query object for use by get_response (or other things)
        """
        raise NotImplementedError("This is an abstract method and must be overridden")

    def get_response(self, page):
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


class AnalyticsQuery(Query):
    metrics = models.CharField(max_length=512,
                               help_text='See https://developers.google.com/analytics/devguides/reporting/core/dimsmets')
    dimensions = models.CharField(max_length=256,
                                  help_text='See https://developers.google.com/analytics/devguides/reporting/core/dimsmets')

    def get_dates(self, campaign):
        try:
            end = campaign.end_date
            start = campaign.start_date
        except:
            end = now()
            start = end - timedelta(30)

        end_date = 'today' if end.date() >= now().date() else end.strftime('%Y-%m-%d')
        start_date = 'today' if start >= now() or self.is_today else start.strftime('%Y-%m-%d')
        if end_date is not 'today':
            start_date = end_date

        return {'start': start_date, 'end': end_date}

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

    def get_query(self, page):
        """
        Gets the query object for this query with the given table id.
        Returns a analytics query object that has an execute method,
            calling analyticsQuery.get_query().execute() will return
            a response (in JSON)
        """
        if 'google_analytics' in page.dashboard_settings:
            table_id = 'ga:' + str(page.dashboard_settings['google_analytics'])
        else:
            return {'error': "please define 'google_analytics' in dashboard page"}

        date = self.get_dates(page.campaign)
        try:
            campaign_id = page.campaign.identifier
        except:
            campaign_id = ''

        # TODO add this in again
        ga_filter = 'ga:sessions>=0' if (campaign_id == '') else ('ga:campaign==' + campaign_id)
        service = AnalyticsQuery.build_analytics()
        data = service.data().ga().get(ids=table_id,
                                       start_date=date['start'],
                                       end_date=date['end'],
                                       metrics=self.metrics,
                                       dimensions=self.dimensions,
                                       output='dataTable')
        return data

    def get_response(self, page):
        response = {'error': 'Failed to retrieve data'}
        try:
            data = self.get_query(page)
            response = data.execute()
        except HttpError as error:
            print "Querying Google Analytics failed with: ", error
            response = dict(response.items() + self.cached_response.items())

        if 'dataTable' in response:
            for header in response['dataTable']['cols']:
                header['label'] = header['label'].split(':')[1]
                # Complicated reg-ex:
                #   first group is all lower case,
                #   second is a single group capital/digit followed by more digits or lower case.
                #   ie. goal2Completions -> [(u'goal', u''), (u'', u'2'), (u'', u'Completions')]
                temp_title = re.findall(r'(^[a-z]*)|([0-9A-Z]{1}[0-9a-z]*)', header['label'])
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
        #TODO fix code for saving... is this even necessary?
        if False:  #not 'error' in response:
            self.cached_response = json.dumps(response)
            self.save()
        return json.dumps(response)


class ClickmeterQuery(Query):
    """
    Currently only supports getting conversions and other data that takes similar parameters
    """
    endpoint = models.CharField(max_length=128)
    group_by = models.CharField(max_length=64)
    id_number = models.IntegerField(default=0,
                                    verbose_name='The index number of the clickmeter_id that this query uses')

    def get_dates(self, campaign):
        try:
            end = campaign.end_date
            start = campaign.start_date
        except:
            end = now()
            start = end - timedelta(30)

        # TODO add logic for is_today here
        end_date = end.strftime('%Y%m%d%H%M')
        start_date = start.strftime('%Y%m%d%H%M')

        return {'start': start_date, 'end': end_date}

    def get_query(self, page):
        """
        Do authentication and then prepare a request. This allows for making requests to any
            Clickmeter endpoint that requires an id, dates, and groupBy.
        """
        # determine if we can get an id. if not return (cause we need one for most requests)
        if 'clickmeter' in page.dashboard_settings:
            try:
                clickmeter_id = page.dashboard_settings['clickmeter'][self.id_number]
            except:
                print 'clickmeter id cannot be found, array is likely out of bounds'
                return {'error': 'id cannot be found'}
        else:
            return {'error': 'id cannot be found'}

        url = 'http://apiv2.clickmeter.com' + str(self.endpoint).format(id=clickmeter_id)
        auth_header = {"X-Clickmeter-Authkey": settings.CLICKMETER_API_KEY}
        dates = self.get_dates(page.campaign)
        data = {'timeframe': 'custom',
                'fromDay': dates['start'],
                'toDay': dates['end']}
        return {'url': url, 'header': auth_header, 'payload': data}

    def get_response(self, page):
        query = self.get_query(page)
        response = json.dumps({'error': 'Failed to retrieve data'})

        try:
            response = requests.get(query['url'], headers=query['header'], params=query['payload'])
        except HttpError as error:
            print "Querying Clickmeter failed with: ", error
        #TODO fix code for saving... is this even necessary?
        if False:  #not 'error' in response:
            self.cached_response = response
            self.save()
        return json.dumps(response.json())


class KeenIOMetricsQuery(Query):
    """
    Apparently we track these in our database with more accuracy so this might be unused
    depending on whether we start using Keen or not
    """
    metric_name = models.CharField(max_length=128)

    event_collection = models.CharField(max_length=128)
    target_property = models.CharField(max_length=128)
    filters = jsonfield.JSONField(default=[], blank=True)
    use_timeframe = models.BooleanField(default=False)
    interval = models.CharField(max_length=16, choices=[
        ('', 'No Interval'),
        ('minutely', 'Every Minute'),
        ('hourly', 'Every Hour'),
        ('daily', 'Each Day'),
        ('weekly', 'Each Week'),
        ('monthly', 'By Month'),
        ('yearly', 'By Year')
    ], default='', blank=True)
    group_by = jsonfield.JSONField(default=[], blank=True)

    def get_dates(self, campaign):
        try:
            end = campaign.end_date
            start = campaign.start_date
        except:
            end = now()
            start = end - timedelta(30)

        end_date = 'today' if end.date() >= now().date() else end.strftime('%Y-%m-%dT%H%MZ')
        start_date = 'today' if start >= now() or self.is_today else start.strftime('%Y-%m-%dT%H%MZ')
        if end_date is not 'today':
            start_date = end_date

        return {'start': start_date, 'end': end_date}

    def get_query(self, page):
        header = {"Authorization": settings.KEEN_CONFIG['readKey']}
        base_url = 'https://api.keen.io/3.0/projects/{project_id}/queries/{metric_name}'
        url = base_url.format(project_id=settings.KEEN_CONFIG['projectId'], metric_name=self.metric_name)
        request_data = {
            'event_collection': self.event_collection,
            'target_property': self.target_property,
        }
        filters = [
            {
                "operator": "eq",
                "property_name": "page.id",
                "property_value": page.id
            },
            {
                "operator": "contains",
                "property_name": "page.url",
                "property_value": page.url_slug
            }
        ]
        filters += self.filters
        request_data.update({'filters': json.dumps(filters)})
        if self.use_timeframe:
            request_data.update({'timeframe': self.get_dates(page.campaign),
                                 'interval': self.interval})
        if self.group_by is not []:
            request_data.update({'group_by': json.dumps(self.group_by)})

        return {'url': url, 'header': header, 'payload': request_data}

    def get_response(self, page):
        query = self.get_query(page)
        response = json.dumps({'error': 'Failed to retrieve data'})

        try:
            response = requests.get(query['url'], headers=query['header'], params=query['payload'])
        except HttpError as error:
            print "Querying Keen.io failed with: ", error

        #TODO fix code for saving... is this even necessary?
        if False:  #not 'error' in response:
            self.cached_response = response
            self.save()
        return json.dumps(response.json())


class Campaign(models.Model):
    title = models.CharField(max_length=128)
    identifier = models.CharField(max_length=128, unique=True)

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
    page = models.ForeignKey('assets.Page', blank=False, null=True)

    queries = models.ManyToManyField(Query)

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
