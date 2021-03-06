import json

from django.http import HttpResponse


class NonHtmlDebugToolbarMiddleware(object):
    """
    The Django Debug Toolbar usually only works for views that return HTML.
    This middleware wraps any non-HTML response in HTML if the request
    has a 'debug' query parameter (e.g. http://localhost/foo?debug)
    Special handling for json (pretty printing) and
    binary data (only show data length)

    Source: http://stackoverflow.com/a/19249559/1558430
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
