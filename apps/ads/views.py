from django.http.response import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render_to_response
import re
from apps.assets.models import Page, Store
from apps.pinpoint.utils import get_store_from_request, get_store_slug_from_hostname

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from django.http import HttpResponse, HttpResponseNotFound

from utils import render_banner


def campaign(request, page_id):
    """Returns a rendered campaign response of the given id.

    :param product: if given, the product is the featured product.
    """
    page = get_object_or_404(Page, id=page_id)
    rendered_content = render_banner(page=page, request=request)

    return HttpResponse(rendered_content)


def demo_page_by_slug(request, ad_id):
    """Determines
    - the site to fake
    - the ad to put in it

    and renders the resultant "demo page" (which is not a Page at all).
    """
    default_demo_page = 'bustle'
    template_slug = get_store_slug_from_hostname(request.get_host()) or default_demo_page

    if not re.match(r'[a-zA-Z0-9-_]+', template_slug):
        # XSS
        return HttpResponseBadRequest()

    return render_to_response(
        '{template_slug}/index.html'.format(template_slug=template_slug),
        {'ad_id': ad_id})
