from django.contrib.auth import BACKEND_SESSION_KEY, SESSION_KEY, load_backend
from django.contrib.auth.decorators import login_required
import httplib2
import os
import json
from apiclient.discovery import build

from django.utils.timezone import now
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User

from oauth2client import xsrfutil
from oauth2client.client import SignedJwtAssertionCredentials
from oauth2client.django_orm import Storage
import re
from string import capitalize

from apps.dashboard.models import CredentialsModel, DashBoard

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


def get_data(request):
    response = {'response': 'Retrieving data failed'}
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

            dash = DashBoard.objects.all()[0]  # TODO this is not the way to get a dashboard

            if True:  # (dash.timeStamp - datetime.utcnow().replace(tzinfo=utc)).seconds > 30:
                service = build_analytics()
                data = service.data().ga().get(ids=table_id,
                                               start_date=start_date,
                                               end_date=end_date,
                                               metrics=metrics,
                                               dimensions=dimension,
                                               output='dataTable')
                response = data.execute()
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
                #TODO save response here
            else:
                # TODO get from database
                pass
    response = json.dumps(response)
    return HttpResponse(response, content_type='application/json')


def index(request):
    context = RequestContext(request)
    return render_to_response('index.html', {}, context)  #this will eventually be different


@login_required
def gap(request):
    context = RequestContext(request)
    return render_to_response('index.html', {}, context)
