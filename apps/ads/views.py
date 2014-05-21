from django.shortcuts import get_object_or_404
from apps.assets.models import Page

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from django.http import HttpResponse

from utils import render_banner


def campaign(request, page_id):
    """Returns a rendered campaign response of the given id.

    :param product: if given, the product is the featured product.
    """
    page = get_object_or_404(Page, id=page_id)
    rendered_content = render_banner(page=page, request=request)

    return HttpResponse(rendered_content)
