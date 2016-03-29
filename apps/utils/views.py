#!/usr/bin/env python
import os
import json

from django.conf import settings
from django.http import HttpResponse


def healthcheck(request):
    """
    Ensure that the revisioned files are collected before
    serving from this instance. If this isn't the case, the
    provisioning failed.

    Strategy: check rev-manifest.json exists in the static directory
    """
    # relative path is from whereever manage.py is being run
    if not os.path.isfile("./apps/light/static/light/rev-manifest.json"):
        return HttpResponse(status=500, reason=u"Couldn't open revision manifest", content="SERVER ERROR")
    else:
        return HttpResponse(status=200, content="OK")
