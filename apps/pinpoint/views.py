from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.http import HttpResponse, Http404
from django.contrib.contenttypes.models import ContentType

from apps.pinpoint.models import Campaign, BlockType, BlockContent
from apps.assets.models import Store, Product

import apps.pinpoint.wizards as wizards


@login_required
def login_redirect(request):
    store_set = request.user.store_set
    if store_set.count() == 1:
        return redirect('store-admin', store_id=str(store_set.all()[0].id))
    else:
        return redirect('admin')


@login_required
def admin(request):
    return render_to_response('pinpoint/admin_staff.html', {
        "stores": request.user.store_set
    }, context_instance=RequestContext(request))


@login_required
def store_admin(request, store_id):
    store = get_object_or_404(Store, pk=store_id)

    if not request.user in store.staff.all():
        raise Http404

    return render_to_response('pinpoint/admin_store.html', {
        "store": store
    }, context_instance=RequestContext(request))


@login_required
def new_campaign(request, store_id):
    store = get_object_or_404(Store, pk=store_id)

    return render_to_response('pinpoint/admin_new_campaign.html', {
        "store": store,
        "block_types": BlockType.objects.all(),
    }, context_instance=RequestContext(request))


@login_required
def campaign_overview(request, store_id, campaign_id):
    store = get_object_or_404(Store, pk=store_id)
    created_campaign = get_object_or_404(Campaign, pk=campaign_id)

    return render_to_response('pinpoint/admin_campaign.html', {
        "store": store,
        "campaign": created_campaign,
        "content_block": created_campaign.content_blocks.all()[0]
    }, context_instance=RequestContext(request))


@login_required
def edit_campaign(request, store_id, campaign_id):
    store = get_object_or_404(Store, pk=store_id)
    campaign_instance = get_object_or_404(Campaign, pk=campaign_id)
    block_type = campaign_instance.content_blocks.all()[0].block_type

    return getattr(wizards, block_type.handler)(
        request, store, block_type, campaign=campaign_instance)


@login_required
def block_type_router(request, store_id, block_type_id):
    store = get_object_or_404(Store, pk=store_id)
    block_type = get_object_or_404(BlockType, pk=block_type_id)

    return getattr(wizards, block_type.handler)(request, store, block_type)


@login_required
def campaign_analytics_admin(request, campaign_id):
    pass


@login_required
def store_analytics_admin(request, store_id):
    pass


def campaign(request, campaign_id):
    campaign_instance = get_object_or_404(Campaign, pk=campaign_id)
    if not request.user in campaign_instance.store.staff.all():
        raise Http404

    return render_to_response('pinpoint/campaign.html', {
        "campaign": campaign_instance,
        "columns": range(4),
        "preview": not campaign_instance.enabled
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
