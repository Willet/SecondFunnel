from apiclient.errors import HttpError
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import cache_page, never_cache
import httplib2
import json
import re

from apiclient.discovery import build

from django.contrib.auth import authenticate, login, logout

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.contrib.auth.models import User
from django.conf import settings

from oauth2client.client import SignedJwtAssertionCredentials

from string import capitalize

from apps.dashboard.models import DashBoard, UserProfile, Campaign, Query
from apps.utils import async

LOGIN_URL = '/dashboard/login'


@cache_page(60*60)  # cache page for an hour
@login_required(login_url=LOGIN_URL)
@never_cache
def get_data(request):
    response = {'error': 'Retrieving data failed'}
    if request.method == 'GET':
        user = User.objects.get(pk=request.user.pk)
        profile = UserProfile.objects.get(user=user)
        request = request.GET

        dashboardId = -1
        if 'dashboard' in request:
            dashboardId = request['dashboard']
        try:
            dashboard = DashBoard.objects.get(pk=dashboardId)
        except DashBoard.MultipleObjectsReturned, DashBoard.DoesNotExist:
            return response

        if('query_name' in request) and ('campaign' in request):
            # get data from ga based on queryName
            campaign_id = request['campaign']
            campaign = Campaign.objects.get(identifier=campaign_id)
            query_name = request['query_name']
            query = Query.objects.get(identifier=query_name)
            # set response
            response = query.get_response(dashboard.table_id, campaign.start_date, campaign.end_date)
    return response


@login_required(login_url=LOGIN_URL)
def index(request):
    user = User.objects.get(pk=request.user.pk)
    context_dict = {}
    try:
        profile = UserProfile.objects.get(user=user)
        dashboards = profile.dashboards.all()
        context_dict = {'dashboards': [{'site': dashboard.site_name,
                                        'pk': dashboard.pk,
                                        'tableId': dashboard.table_id} for dashboard in dashboards]}
    except UserProfile.DoesNotExist:
        print "user does not exist"

    context = RequestContext(request)
    return render_to_response('index.html', context_dict, context)


@login_required(login_url=LOGIN_URL)
def dashboard(request, dashboardId):
    profile = UserProfile.objects.get(user=request.user)
    if not profile.dashboards.all().filter(pk=dashboardId):
        # can't view page
        return HttpResponseRedirect('/dashboard/')
    else:
        context_dict = {}
        try:
            dashboard = DashBoard.objects.get(pk=dashboardId)
        except DashBoard.MultipleObjectsReturned or DashBoard.DoesNotExist:
            return HttpResponseRedirect('/dashboard/')
        context_dict['tableId'] = dashboard.table_id
        context_dict['siteName'] = dashboard.site_name
        # TODO add this to model
        context_dict['campaigns'] = [{'name': 'Lived In', 'value': 'livedin'},
                                     {'name': 'Summer Loves', 'value': 'summerloves'},
                                     {'name': 'Paddington Bear', 'value': 'paddington'},
                                     {'name': 'President', 'value': 'president'}]

        return render(request, 'dashboard.html', context_dict)


def user_login(request):
    context = RequestContext(request)

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # authenticate username/password combo, store user
        user = authenticate(username=username, password=password)

        if user is not None:  # if authentication was successful
            if user.is_active:  # could have been deactivated
                login(request, user)  # log the user in.
                return HttpResponseRedirect('/dashboard/')
            else:  # user account was deactivated
                return HttpResponse("Your SecondFunnel account is disabled")

        else:  # invalid account
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    else:  # display form. most likely http GET
        return render_to_response('login.html',
                                  {},  # no context variables to pass
                                  context)


@login_required(login_url=LOGIN_URL)
def user_logout(request):
    logout(request)
    # Take the user back to the homepage.
    return HttpResponseRedirect('/dashboard/')


######## LEGACY CODE ########

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


def prettify_data(response):
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
    return response

@cache_page(60*60)  # cache page for an hour
@login_required(login_url=LOGIN_URL)
@never_cache
def get_data_old(request):
    response = {'error': 'Retrieving data failed'}
    if request.method == 'GET':
        GET_REQUEST = request.GET

        if ('table' in GET_REQUEST) and \
                ('metrics' in GET_REQUEST) and ('dimension' in GET_REQUEST) and \
                ('start-date' in GET_REQUEST) and ('end-date' in GET_REQUEST):

            table_id = 'ga:' + GET_REQUEST['table']
            metrics = GET_REQUEST['metrics']
            dimension = GET_REQUEST['dimension']
            start_date = GET_REQUEST['start-date']
            end_date = GET_REQUEST['end-date']

            service = build_analytics()
            data = service.data().ga().get(ids=table_id,
                                           start_date=start_date,
                                           end_date=end_date,
                                           metrics=metrics,
                                           dimensions=dimension,
                                           output='dataTable')
            try:
                response = prettify_data(data.execute())
            except HttpError as error:
                print "Querying Google Analytics failed with: ", error
                response['error'] = 'Querying GA failed'
    response = json.dumps(response)
    return HttpResponse(response, content_type='application/json')
