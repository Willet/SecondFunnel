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
from oauth2client.client import flow_from_clientsecrets
from oauth2client.django_orm import Storage
import re
from string import capitalize

from apps.dashboard.models import CredentialsModel, DashBoard

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secret.json')
redirect = settings.WEBSITE_BASE_URL + '/dashboard/oath2callback'

FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/analytics.readonly',
    redirect_uri=redirect)


def index(request):
    context = RequestContext(request)
    return render_to_response('index.html', {}, context)  #this will eventually be different


@login_required
def gap(request):
    user = request.user
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    credential = storage.get()
    if credential is None or credential.invalid:
        print "Credential is invalid, retrieving new token"
        FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                       user)
        authorize_url = FLOW.step1_get_authorize_url()
        return HttpResponseRedirect(authorize_url)
    else:
        context = RequestContext(request)
        return render_to_response('index.html', {}, context)


def auth_return(request):
    if not xsrfutil.validate_token(settings.SECRET_KEY, request.REQUEST['state'],
                                   request.user.id):
        return HttpResponse("bad request")
    credential = FLOW.step2_exchange(request.REQUEST)
    storage = Storage(CredentialsModel, 'id', request.user, 'credential')
    storage.put(credential)
    return HttpResponseRedirect("/dashboard")

@login_required
def get_data(request):
    response = {'response': 'Retrieving data failed'}

    user = request.user
    storage = Storage(CredentialsModel, 'id', user, 'credential')
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
                credential = storage.get()
                if credential is None or credential.invalid:
                    print "Credential is invalid at retrieval"
                    #FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                    #                                               user)
                    #authorize_url = FLOW.step1_get_authorize_url()
                    return HttpResponseRedirect('/dashboard')  # TODO to login page or error
                else:
                    http = httplib2.Http()
                    http = credential.authorize(http)
                    service = build("analytics", "v3", http=http)
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
