from functools import partial
import json
from django.contrib import messages
from django.template.defaultfilters import slugify, safe
import re

from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext, Template, Context, loader
from django.http import HttpResponse, Http404
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page

from apps.analytics.models import Category, AnalyticsRecency
from apps.assets.models import Store, Product
from apps.pinpoint.models import Campaign, BlockType, BlockContent
from apps.pinpoint.decorators import belongs_to_store

import apps.pinpoint.wizards as wizards
from apps.utils import noop
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


# origin: campaigns with short URLs are cached for 30 minutes
@cache_page(60 * 30)
def campaign_short(request, campaign_id_short):
    """base62() is a custom function, so to figure out the long
    campaign URL, go to http://elenzil.com/esoterica/baseConversion.html
    and decode with the base in utils/base62.py.

    The long URL is (currently) /pinpoint/(long ID).
    """
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
    if context is None:
        context = Context()
    context.update(arguments)

    # TODO: Content blocks don't make as much sense now; when to clean up?
    # TODO: If we keep content blocks, should this be a method?
    # Assume only one content block
    content_block = campaign.content_blocks.all()[0]

    product = content_block.data.product
    product.json = json.dumps(product.data(raw=True))

    campaign.stl_image = getattr(content_block.data, 'get_ls_image', noop)(url=True) or ''
    campaign.featured_image = getattr(content_block.data, 'get_image', noop)(url=True) or ''
    campaign.description = safe(content_block.data.description or product.description)
    campaign.template = slugify(content_block.block_type.name)

    context.update({
        'product': product,
        'campaign': campaign
    })

    theme = campaign.store.theme
    page_str = theme.page

    actions = {
        'template': loader.get_template,
        'theme': partial(getattr, theme)
    }

    # Replace necessary tags
    for field, details in theme.REQUIRED_FIELDS.iteritems():
        type = details.get('type')
        values = details.get('values')

        sub_values = []
        for value in values:
            result = actions.get(type)(value)

            # TODO: Do we need to render, or can we just convert to string?
            if isinstance(result, Template):
                result = result.render(context)
            else:
                result = result.encode('unicode-escape')

            sub_values.append(result)

        regex = r'\{\{\s*' + field + '\s*\}\}'
        page_str= re.sub(regex, ''.join(sub_values), page_str)

    # Page content
    page = Template(page_str)

    # Render response
    return HttpResponse(page.render(context))
