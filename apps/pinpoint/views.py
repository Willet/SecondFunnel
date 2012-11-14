import re
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext, Template, Context
from django.http import HttpResponse, Http404
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string

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

    arguments = {
        "campaign": campaign_instance,
        "columns": range(4),
        "preview": not campaign_instance.live
    }
    context = RequestContext(request)

    if hasattr(campaign_instance.store, "theme"):
        context.update(arguments)
        return campaign_to_theme_to_response(campaign_instance, arguments,
                                             context_instance=context)
    else:
        return render_to_response('pinpoint/campaign.html', arguments,
                                  context_instance=context)

def campaign_to_theme_to_response(campaign, arguments, context_instance=None):
    if context_instance is None:
        context_instance = Context()

    context_instance.update(arguments)

    theme = campaign.store.theme

    # Determine featured content type
    for block in campaign.content_blocks.all():
        content_type = block.content_type.name
        if content_type != "campaign":
            break

    content_template = {
        'featured product block': theme.featured_product
    }.get(content_type)

    # Pre-render sub-templates
    header    = Template('').render(context_instance)
    featured  = Template(content_template).render(context_instance)
    discovery = Template('').render(context_instance)

    # Replace necessary tags
    modified_page = re.sub(r'{% ?include header_content ?%}',
                           header, theme.page_template)
    modified_page = re.sub(r'{% ?include featured_content ?%}',
                           featured, modified_page)
    modified_page = re.sub(r'{% ?include discovery_area ?%}',
                           discovery, modified_page)

    # Render page
    page = Template(modified_page, name='campaign')

    # Render response
    return HttpResponse(page.render(context_instance))