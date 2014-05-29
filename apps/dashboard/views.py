import httplib2
import os
import json
from apiclient.discovery import build

from datetime import datetime
from django.utils.timezone import utc
from django.conf import settings
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User

from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.django_orm import Storage
import re

from apps.dashboard.models import CredentialsModel, DashBoard

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secret.json')


FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/analytics.readonly',
    redirect_uri=settings.WEBSITE_BASE_URL + '/dashboard/oauth2callback')


def index(request):
    context = RequestContext(request)
    return render_to_response('index.html', {}, context)  #this will eventually be different


def gap(request):
    storage = Storage(CredentialsModel, 'id', request.user, 'credential')
    credential = storage.get()
    if credential is None or credential.invalid == True:
        FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                       request.user)
        authorize_url = FLOW.step1_get_authorize_url()
        return HttpResponseRedirect(authorize_url)
    context = RequestContext(request)
    return render_to_response('index.html', {}, context)


def auth_return(request):
    if not xsrfutil.validate_token(settings.SECRET_KEY, request.REQUEST['state'],
                                 request.user):
        return HttpResponseBadRequest()
    credential = FLOW.step2_exchange(request.REQUEST)
    storage = Storage(CredentialsModel, 'id', request.user, 'credential')
    storage.put(credential)
    return HttpResponseRedirect("/dashboard")


def get_data(request):
    response = {'response': 'Retrieving data failed'}

    if request.method == 'GET':
        user = request.user
        storage = Storage(CredentialsModel, 'id', user, 'credential')
        request = request.GET

        if ('table' in request) and \
                    ('metrics' in request) and ('dimension' in request) and \
                    ('start-date' in request) and ('end-date' in request):

            table_id = 'ga:' + request['table']
            metrics = request['metrics']
            dimension = request['dimension']
            start_date = request['start-date']
            end_date = request['end-date']

            dash = DashBoard.objects.all()[0]

            if (dash.timeStamp - datetime.utcnow().replace(tzinfo=utc)).seconds > 30:
                # TODO Save response in database?
                credential = storage.get()
                if credential is None or credential.invalid:
                    print "Credential is invalid, retrieving new token"
                    FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                                   user)
                    authorize_url = FLOW.step1_get_authorize_url()
                    return HttpResponseRedirect(authorize_url)
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
            else:
                # TODO get response from database. right now just get response from server
                credential = storage.get()
                if credential is None or credential.invalid:
                    print "Credential is invalid, retrieving new token"
                    FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                                   request.user)
                    authorize_url = FLOW.step1_get_authorize_url()
                    return HttpResponseRedirect(authorize_url)
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
    #for header in response['dataTable']['cols']:
    #    header['label'] = header['label'].lstrip('ga:')
    #    header['label'] = ' '.join(re.findall(r'(^[a-z]*)|([\dA-Z]{1}[\da-z]*)', header['label'])).strip()
    #    print header['label']
    response = json.dumps(response)
    return HttpResponse(response, content_type='application/json')
