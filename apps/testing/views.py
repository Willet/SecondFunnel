from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.core.management import call_command

from apps.utils.ajax import ajax_error, ajax_success
from apps.testing.utils import parse_results, extension
from settings import CONFIG_DIRS

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import xml.etree.ElementTree as ET
import os
import json
import urllib


def fire_test( request ):
    """
    Calls Django to run the JavaScript tests using the JsTestDriver, and returns
    an appropriate ajax status.

    @param request: The request being made
    @return: ajax
    """
    try:
        tests = urllib.unquote(request.GET['tests'])
        config = urllib.unquote(request.GET['config'])

        if 'browsers' in request.GET:
            browsers = urllib.unquote(request.GET['browsers']).split()
            call_command('jstest', tests=tests, config=config, browsers=browsers, log=True)
        else:
            call_command('jstest', tests=tests, config=config, log=True)

    except BaseException as e:
        return ajax_error({'error': str(e)})

    return ajax_success({'params': request.GET})


def test_results( request ):
    """
    Displays the results of the tests by reading the XML files and
    parsing them.  Result types are "Passed, Skipped, Error".

    @param request: The HTTP request
    @return: HTTPResponse
    """
    data = parse_results()
    configs = []
    for dir in CONFIG_DIRS:
        for (dirpath, dirname, filenames) in os.walk(os.path.join('apps/testing', dir), True):
            for fname in filenames:
                if not extension(fname) == "yaml":
                    continue
                configs.append(os.path.join(dir, fname.rstrip(".yaml")))

    return render_to_response(
        'testing/test.html', {
            'data': data,
            'configs': configs
        },
        context_instance=RequestContext(request),
    )
