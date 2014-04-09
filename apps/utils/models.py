# http://stackoverflow.com/a/19249559/1558430
from django.core.cache import cache
from django.http import HttpResponse
import json


class NonHtmlDebugToolbarMiddleware(object):
    """
    The Django Debug Toolbar usually only works for views that return HTML.
    This middleware wraps any non-HTML response in HTML if the request
    has a 'debug' query parameter (e.g. http://localhost/foo?debug)
    Special handling for json (pretty printing) and
    binary data (only show data length)
    """

    @staticmethod
    def process_response(request, response):
        if request.GET.get('_debug') == '':
            if response['Content-Type'] == 'application/octet-stream':
                new_content = '<html><body>Binary Data, ' \
                    'Length: {}</body></html>'.format(len(response.content))
                response = HttpResponse(new_content)
            elif response['Content-Type'] != 'text/html':
                content = response.content
                try:
                    json_ = json.loads(content)
                    content = json.dumps(json_, sort_keys=True, indent=2)
                except ValueError:
                    pass
                response = HttpResponse('<html><body><pre>{}'
                                        '</pre></body></html>'.format(content))

        return response


class ShowHandlerMiddleware(object):
    """If in dev, reveal which handler processed the request."""
    @staticmethod
    def process_response(request, response):
        try:
            response['Handler'] = request.resolver_match.view_name
        except:
            pass

        return response


class MemcacheSetting(object):
    """Memcache setting wrapper that does not access the DB, which expires
    every half hour.

    If you don't have memcache, nothing happens.
    """

    #@classattribute
    settings = []

    setting_name = None

    @classmethod
    def get(cls, setting_name, default):
        """
        Defaults are REQUIRED; None means cache miss.
        """
        result = cache.get(setting_name, default=default)
        cls._add_key(setting_name)
        return result

    @classmethod
    def set(cls, setting_name, setting_value=None):
        """None is Django's signal for a cache miss. DO NOT STORE NONES."""
        if setting_value == None:
            cache.delete(setting_name)
        else:
            cls._add_key(setting_name)
            cache.set(setting_name, setting_value, timeout=1800)

        return cls

    @classmethod
    def keys(cls):
        """Retrieves a list of keys memcached manually."""
        if not cls.settings:
            keys_ = cls.get('memcached_keys', '').split(',')
            cls.settings = keys_

        return cls.settings

    @classmethod
    def _add_key(cls, key):
        cls.settings.append(key)
        cls.settings = list(set(cls.settings))
        cache.set('memcached_keys', ','.join(cls.settings), timeout=10000)
