import apiclient
import httplib2
from oauth2client import xsrfutil
import os

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from django.contrib.auth.models import User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.django_orm import Storage

from apps.dashboard.models import CredentialsModel

from apps.assets.models import Tile

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), '..', 'client_secrets.json')

print CLIENT_SECRETS

FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/analytics.readonly',
    redirect_uri='http://localhost:8000/dashboard/oauth2callback')


def summerloves(request):
    context = RequestContext(request)
    return render_to_response('index.html', {}, context)


def testAnalytics(request):
    storage = Storage(CredentialsModel, 'id', request.user, 'credential')

    credential = storage.get()
    if credential is None or credential.invalid == True:
        FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                       request.user)
        authorize_url = FLOW.step1_get_authorize_url()
        return HttpResponseRedirect(authorize_url)
    else:
        http = httplib2.Http()
        http = credential.authorize(http)
        service = apiclient.discovery.build("plus", "v1", http=http)
        activities = service.activities()
        activitylist = activities.list(collection='public',
                                       userId='me').execute()
        logging.info(activitylist)

    return render_to_response('plus/welcome.html', {
        'activitylist': activitylist,
    })
    pass


def auth_return(request):
    pass