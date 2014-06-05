from apiclient.errors import HttpError
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
import httplib2
import os
import json
import re

from apiclient.discovery import build

from django.contrib.auth import authenticate, login, logout

from django.utils.timezone import now
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.contrib.auth.models import User

from oauth2client.client import SignedJwtAssertionCredentials

from string import capitalize

from apps.dashboard.models import DashBoard, UserProfile

LOGIN_URL = '/dashboards/login'
SERVICE_ACCOUNT_EMAIL = "231833496051-kf5r0aath3eh96209hdutfggj5dqld9f@developer.gserviceaccount.com"
SERVICE_ACCOUNT_PKCS12_FILE_PATH = os.path.join(os.path.dirname(__file__),
                                                'ad04005e5e7b5a51c66cd176e10277a59cb61824-privatekey.p12')


def build_analytics():
    """
    Builds and returns an Analytics service object authorized with the given service account
    Returns a service object
    """
    f = open(SERVICE_ACCOUNT_PKCS12_FILE_PATH, 'rb')
    key = f.read()
    f.close()

    credentials = SignedJwtAssertionCredentials(SERVICE_ACCOUNT_EMAIL,
                                                key,
                                                scope='https://www.googleapis.com/auth/analytics.readonly')
    http = httplib2.Http()
    http = credentials.authorize(http)

    return build('analytics', 'v3', http=http)


def prettify_data(response):
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
        header['label'] = title
    return response


@login_required(login_url=LOGIN_URL)
@cache_page(60 * 60)  # cache for an hour
def get_data(request):
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

            #dash = DashBoard.objects.all()[0]  # TODO this is not the way to get a dashboard

            if True:  # (dash.timeStamp - datetime.utcnow().replace(tzinfo=utc)).seconds > 30:
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

                #TODO save response here if caching doesn't work
            else:
                # TODO get from database
                pass
    response = json.dumps(response)
    return HttpResponse(response, content_type='application/json')

@login_required(login_url=LOGIN_URL)
def index(request):
    user = User.objects.get(pk=request.user.pk)
    context_dict = {}
    try:
        profile = UserProfile.objects.get(user=user)
        dashboards = profile.dashboards.all()
        context_dict = {'dashboards': [{'site': dashboard.site,
                                       'tableId': dashboard.table_id} for dashboard in dashboards]}
    except UserProfile.DoesNotExist:
        print "user does not exist"

    context = RequestContext(request)
    return render_to_response('index.html', context_dict, context)


def gap(request):
    return render(request, 'dashboard.html',)


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
                return HttpResponseRedirect('/dashboards/')
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
    return HttpResponseRedirect('/dashboards/')
