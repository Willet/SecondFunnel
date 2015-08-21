import gzip
import json
import StringIO
import urllib2

from datetime import datetime
from django.db.models import Q
from os import path

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template import RequestContext, Template
from django.utils.safestring import mark_safe
import re

from apps.assets.models import Page, Store, Product
from apps.intentrank.serializers import PageConfigSerializer


def read_a_file(file_name, default_value=''):
    """just a file opener with a catch."""
    try:
        with open(path.abspath(file_name)) as f:
            return f.read()
    except (IOError, TypeError):
        return default_value


def read_remote_file(url, default_value=''):
    """
    Url opener that reads a url and gets the content body.
    Returns a tuple response where the first item is the data and the
    second is whether the response was gzipped or not.
    """
    try:
        request = urllib2.Request(url)
        request.add_header('Accept-encoding', 'gzip')
        # in case Python-urllib/2.6 would be rejected
        request.add_header('User-agent', 'Mozilla/5.0')
        response = urllib2.urlopen(request)

        if not 200 <= int(response.getcode()) <= 300:
            return default_value, False

        if response.info().get('Content-Encoding') == 'gzip':
            buf = StringIO.StringIO(response.read())
            zfile = gzip.GzipFile(fileobj=buf)
            content = zfile.read()
            zfile.close()
            return content, True

        content = response.read()
        return content, False
    except (TypeError, ValueError, urllib2.HTTPError):
        return default_value, False


def get_store_slug_from_hostname(hostname):
    hostpart_blacklist = ['demo', 'secondfunnel', 'stage']
    if settings.ENVIRONMENT == 'dev':
        # 2ndfunnel is just for debugging. sorry
        hostpart_blacklist.append('2ndfunnel')

    # matches either
    matches = re.match(r'(?:https?://)?([^:]+)(?::\d+)?', hostname, re.I)
    slug = ''
    if not matches:
        return ''
    parts = matches.group(1).split('.')

    # necessary because this is supposed to return 'newegg' in 'explore.newegg.com'
    # and 'gap' in 'gap.secondfunnel.com' or 'gap.demo.secondfunnel.com'
    for part in parts[:-1]:  # removes last part (TLD)
        if not part in hostpart_blacklist:
            slug = part
    return slug


def get_store_from_request(request):
    """
    Returns the store pointed to by the request host if it exists.
    Requests forwarded from CloudFront set the HTTP_ORIGIN header
    to the original host.
    """
    if request.META.get('HTTP_USER_AGENT', '') == settings.CLOUDFRONT_USER_AGENT:
        current_url = request.META.get('HTTP_ORIGIN',
                                       request.META.get('HTTP_HOST', ''))
    else:
        current_url = 'http://%s/' % request.get_host()

    try:
        slug = get_store_slug_from_hostname(current_url)
        store = Store.objects.get(Q(public_base_url=current_url) | Q(slug=slug))
    except Store.DoesNotExist:
        store = None

    return store


def get_algorithm(algorithm=None, request=None, page=None, feed=None):
    """Given one or more conditions, return the algorithm with the highest
    precedence.

    Priority:
    - if you specify one
    - if request specifies one
    - if page settings specify one
    - if feed has one
    - 'magic'

    :returns str
    """
    if algorithm:
        return algorithm

    if request and request.GET.get('algorithm'):
        return request.GET.get('algorithm', 'magic')

    if page and page.theme_settings.get('feed_algorithm'):
        return page.theme_settings.get('feed_algorithm')

    if not feed and page:
        feed = page.feed

    if feed and feed.feed_algorithm:
        return feed.feed_algorithm

    return 'magic'
