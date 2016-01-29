from django.conf import settings


class BrowserSyncMiddleware(object):
    """
    Middleware to inject BrowerSync used by light integration
    for auto-reloading purposes.
    """

    injected_content = """
<script type='text/javascript'>//<![CDATA[
;document.write("<script async src='//HOST:3000/browser-sync-client.1.3.6.js'><\/script>".replace(/HOST/g, location.hostname));
//]]></script>
    """

    def process_response(self, request, response):
        if request.is_ajax() or\
           request.META.get('REMOTE_ADDR', None) not in settings.INTERNAL_IPS or\
           not bool(settings.DEBUG):
            return response

        # verify we are working with some html
        ctype = response.get('Content-Type', '').lower()
        if ctype != "text/html" and not ctype.startswith("text/html;"):
            return response

        # If encoding is already set, we should not modify response
        if response.has_header('Content-Encoding'):
            return response

        # flatten the content (ikr, this looks like it does nothing)
        content = response.content
        response.content = content

        # find the end of <head> tag
        head_end = content.find('</head>')
        if head_end != -1:
            content = ''.join([content[0:head_end], self.injected_content, content[head_end:]])
            response.content = content

        return response
