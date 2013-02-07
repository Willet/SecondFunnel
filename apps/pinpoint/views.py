from django.contrib import messages
import re

from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext, Template, Context
from django.http import HttpResponse, Http404
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page

from apps.analytics.models import Category, AnalyticsRecency
from apps.assets.models import Store, Product
from apps.pinpoint.models import Campaign, BlockType, BlockContent
from apps.pinpoint.decorators import belongs_to_store

import apps.pinpoint.wizards as wizards
import apps.utils.base62 as base62


@login_required
def login_redirect(request):
    """
    Redirects user to store admin page if they are only staff for one store.

    @param request: The request for this page.

    @return: An HttpResponseRedirect that redirects the user to either a store admin
    page, or a page where the user can pick which store they want to view.
    """
    store_set = request.user.store_set
    if store_set.count() == 1:
        return redirect('store-admin', store_id=str(store_set.all()[0].id))
    else:
        return redirect('admin')


@login_required
def admin(request):
    """
    Allows the user to select which store they want to view.

    @param request: The request for this page.

    @return: An HttpResponse which renders the page template.
    """
    return render_to_response('pinpoint/admin_staff.html', {
        "stores": request.user.store_set
    }, context_instance=RequestContext(request))


@belongs_to_store
@login_required
def store_admin(request, store_id):
    """
    Displays the pinpoint pages for the given store. User can make new pages,
    edit pages, and get links to pages.

    @param request: The request for this page.
    @param store_id: The id of the store to show pinpoint pages for.

    @return: An HttpResponse which renders the page template.
    """
    store = get_object_or_404(Store, pk=store_id)

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
def delete_campaign(request, store_id, campaign_id):
    campaign_instance = get_object_or_404(Campaign, pk=campaign_id)
    campaign_instance.live = False
    campaign_instance.save()

    messages.success(request, "Your page was deleted.")

    return redirect('store-admin', store_id=store_id)


@login_required
def block_type_router(request, store_id, block_type_id):
    """Resolves the handler that renders a "block type".

    Handler information is stored in the database.
    """
    store = get_object_or_404(Store, pk=store_id)
    block_type = get_object_or_404(BlockType, pk=block_type_id)

    return getattr(wizards, block_type.handler)(request, store, block_type)


@login_required
def store_analytics_admin(request, store_id):
    store = get_object_or_404(Store, pk=store_id)

    return analytics_admin(request, store)


@login_required
def campaign_analytics_admin(request, store_id, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)

    return analytics_admin(
        request, campaign.store, campaign=campaign, is_overview=False)


@belongs_to_store
@login_required
def analytics_admin(request, store, campaign=False, is_overview=True):
    categories = Category.objects.filter(enabled=True)
    store_type = ContentType.objects.get_for_model(Store)
    campaign_type = ContentType.objects.get_for_model(Campaign)

    try:
        if campaign:
            recency = AnalyticsRecency.objects.get(
                content_type=campaign_type,
                object_id=campaign.id
            )
        else:
            recency = AnalyticsRecency.objects.get(
                content_type=store_type,
                object_id=store.id
            )
    except AnalyticsRecency.DoesNotExist:
        recency = None
    else:
        recency = recency.last_fetched

    return render_to_response('pinpoint/admin_analytics.html', {
        'is_overview': is_overview,
        'store': store,
        'campaign': campaign,
        'categories': categories,
        'last_updated': recency
    }, context_instance=RequestContext(request))


@cache_page(60 * 30)
def campaign_short(request, campaign_id_short):
    return campaign(request, base62.decode(campaign_id_short))


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
                                             context)
    else:
        return render_to_response('pinpoint/campaign.html', arguments,
                                  context_instance=context)

def campaign_to_theme_to_response(campaign, arguments, context=None):
    """Generates the HTML page for a standard pinpoint product page."""
    if context is None:
        context = Context()
    context.update(arguments)

    # retrieve theme for the store from the DB
    theme = campaign.store.theme

    # Determine featured content type
    # TODO: How to handle multiple block types?
    for block in campaign.content_blocks.all():
        if block.content_type.name != "campaign":
            content_block = block
            break

    featured_context = Context()
    type = content_block.content_type.name

    if type in ('featured product block', 'shop the look block'):
        content_template = theme.featured_product
        product          = content_block.data.product

        # TODO: Is the featured image always in the list of images?
        featured_image   = content_block.data.get_image().get_url()

        product.description    = content_block.data.description
        product.featured_image = featured_image
        product.is_featured    = True

        # Piggyback off of featured product block
        if type == 'shop the look block':
            lifestyle_image = content_block.data.get_ls_image().get_url()
            product.lifestyle_image = lifestyle_image

        featured_context.update({
            'product': product,
        })
    else:
        product = {
            'title': "Unknown Product",
            'url': 'http://secondfunnel.com',
            'featured_image': '',
            'description': 'Unknown Product'
        }


    # Pre-render templates; bottom up
    # Discovery block
    discovery_block = theme.discovery_product # TODO: Generalize to other blocks
    modified_discovery = "".join([
        "{% extends 'pinpoint/campaign_discovery.html' %}",
        "{% load pinpoint_ui %}",
        "{% block discovery_block %}",
        discovery_block,
        "{% endblock discovery_block %}"
    ])

    # Discovery area
    discovery_area = Template(modified_discovery).render(context)

    # Preview block
    # TODO: Does this actually need any additional context?
    modified_preview = "".join([
        "<div class='preview product' style='display: none;'>",
        "<div class='mask'></div>",
        "<div class='tablecell'>",
        "<div class='content'>",
        "<span class='close'>X</span>",
        theme.preview_product,
        "</div>",
        "</div>",
        "</div>"
    ]);
    product_preview = Template(modified_preview).render(context)

    # Featured content
    modified_featured = "".join([
        "{% load pinpoint_ui %}",
        "<div class='featured product' {{ product.data|safe }}>",
        content_template,
        "</div>"
    ])

    featured_content  = Template(modified_featured).render(featured_context)

    # Header content
    header_context = Context(featured_context)
    header_context.update({
        'campaign': campaign,
        'product': product,
        'store': campaign.store
    })

    header_content = render_to_string('pinpoint/campaign_head.html',
                                      arguments, header_context)

    # Scripts
    header_context.update({
        'ga_account_number': settings.GOOGLE_ANALYTICS_PROPERTY
    })
    scripts_content = render_to_string('pinpoint/campaign_scripts.html',
                                      arguments, header_context)

    page_context = Context({
        'featured_content': featured_content,
        'discovery_area': discovery_area,
        'preview_area': product_preview,
        'header_content': header_content,
        'scripts_content': scripts_content
    })

    # Page content
    page = Template(theme.page_template)

    # Render response
    return HttpResponse(page.render(page_context))
