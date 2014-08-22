import re

from django.http import HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.views.decorators.cache import cache_page, cache_control

from apps.assets.models import Page
from apps.light.utils import get_store_slug_from_hostname


@cache_control(must_revalidate=True, max_age=(1 * 60))
@cache_page(60 * 10, key_prefix="demo-")
def demo_page_by_slug(request, ad_slug, template_slug=None):
    """Determines
    - the site to fake
    - the ad to put in it

    and renders the resultant "demo page" (which is not a Page at all).
    """
    default_demo_page = 'bustle'
    hostname = request.get_host()
    ad = Page.objects.get(url_slug=ad_slug)
    if not hostname.startswith('http'):
        # urlparse goes full derp here by returning http:/// <-- 3 slashes
        hostname = 'http://{}'.format(hostname)

    if not template_slug:
        template_slug = get_store_slug_from_hostname(hostname=hostname) \
            or default_demo_page

    if not re.match(r'[a-zA-Z0-9-_]+', template_slug):
        # XSS
        return HttpResponseBadRequest()

    return render_to_response(
        'light/{template_slug}/index.html'.format(template_slug=template_slug),
        {'ad_id': ad.id, 'hostname': hostname})
