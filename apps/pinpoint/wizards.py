from django.shortcuts import render_to_response
from django.template import RequestContext

from apps.pinpoint.models import BlockType


def featured_product_wizard(request, store, block_type):
    return render_to_response('pinpoint/wizards/%s/ui.html' % block_type.slug, {
        "store": store,
        "block_types": BlockType.objects.all(),
        "products": store.product_set.all(),
    }, context_instance=RequestContext(request))
