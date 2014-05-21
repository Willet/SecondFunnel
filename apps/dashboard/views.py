from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from apps.assets.models import Tile


def summerloves(request):
    context = RequestContext(request)
    return render_to_response('index.html', {}, context)