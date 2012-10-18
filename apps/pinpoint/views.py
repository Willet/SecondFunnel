from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.contenttypes.models import ContentType

from apps.pinpoint.models import Campaign, BlockType, BlockContent
from apps.assets.models import Product

def campaign(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    return render_to_response('pinpoint/campaign.html', {
        "campaign": campaign,
        "columns": range(4),
    }, context_instance=RequestContext(request))

def pinpoint_admin(request, campaign_id):
    return render_to_response('pinpoint/admin.html', {
        "storeUrl": campaign_id,
        "pageNames": [],
        "pages": [],
    }, context_instance=RequestContext(request))

def generic_page(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    store = product.store
    block_type = BlockType(name="generic")
    block = BlockContent(
            block_type=block_type,
            content_type=ContentType.objects.get_for_model(Product),
            object_id=product.id)
    return render_to_response('pinpoint/campaign.html', {
        "campaign": {
            "store": store,
            },
        "columns": range(4),
        "content": block
    }, context_instance=RequestContext(request))
