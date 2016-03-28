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

    Strategy: open rev-manifest.json and see if the files
    in it exist in the static directory
    """
    #if settings.ENVIRONMENT == "production":
        # relative path is from whereever manage.py is being run
    try:
        with open("./apps/light/static/light/rev-manifest.json") as f:
            manifest = json.load(f)
            manifest_collected = [os.path.isfile(reved_file) for reved_file in manifest.values()]
            if False in manifest_collected:
                return HttpResponse(status=500,
                                    reason=u"{} out of {} revisioned files not collected".format(
                                        manifest_collected.count(False), len(manifest)),
                                    content="SERVER ERROR")
    except IOError:
        return HttpResponse(status=500, reason=u"Couldn't open revision manifest", content="SERVER ERROR")
                
    # stage or dev
    return HttpResponse(status=200, content="OK")
