import json
import os
import re

from functools import partial
from django.contrib import messages
from django.template.defaultfilters import slugify, safe

from storages.backends.s3boto import S3BotoStorage

from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext, Template, Context, loader
from django.http import HttpResponse, HttpResponseServerError
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.cache import cache_page
from social_auth.db.django_models import UserSocialAuth

from apps.analytics.models import Category, AnalyticsRecency
from apps.assets.models import Store, Product
from apps.intentrank.views import get_seeds
from apps.assets.models import ExternalContent, ExternalContentType
from apps.pinpoint.models import Campaign, BlockType
from apps.pinpoint.decorators import belongs_to_store

import apps.pinpoint.wizards as wizards
from apps.utils import noop
import apps.utils.base62 as base62
from apps.utils.social.instagram_adapter import Instagram


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
def social_auth(request):
    """
    Redirect after some social action (account association, probably).

    @param request: The request for this page.

    @return: An HttpResponse that redirects the user to the asset_manager
    page, or a page where the user can pick which store they want to view
    """
    store_set = request.user.store_set
    if store_set.count() == 1:
        return redirect('asset-manager', store_id=str(store_set.all()[0].id))
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

    return render_to_response('pinpoint/admin_analytics.html', {
        'is_overview': is_overview,
        'store': store,
        'campaign': campaign,
        'categories': categories
    }, context_instance=RequestContext(request))


@belongs_to_store
@login_required
def asset_manager(request, store_id):
    """renders the page that allows store owners to tag their instagram photos
    on their products (or, logically, the other way around).
    """
    store = get_object_or_404(Store, pk=store_id)
    user = request.user

    # Check if connected to Instagram... for now
    try:
        instagram_user = store.social_auth.get(provider='instagram')
    except UserSocialAuth.DoesNotExist:
        instagram_user = None

    if not instagram_user:
        try:
            instagram_user = user.social_auth.get(provider='instagram')
        except UserSocialAuth.DoesNotExist:
            instagram_user = None

    instagram_connect_request = True
    if instagram_user:
        instagram_connect_request = False
        instagram_connector = Instagram(tokens=instagram_user.tokens)
        contents = instagram_connector.get_content(limit=20)
    else:
        contents = []  # also "0 photos"

    return render_to_response('pinpoint/asset_manager.html', {
        "store": store,
        "instagram_connect_request": instagram_connect_request,
        "contents": contents,
        "store_id": store_id
    }, context_instance=RequestContext(request))


@belongs_to_store
@login_required
def tag_content(request, store_id):
    """Adds the instagram photo to a product """
    instagram_json = request.POST.get('instagram')
    product_id = request.POST.get('product_id', -1)

    product = Product.objects.get(id=product_id)

    if not product or not instagram_json:
        messages.error(request, "Missing product or selected content.")
        return redirect('asset-manager', store_id=store_id)

    instagram_content = json.loads(instagram_json)
    for instagram_obj in instagram_content:
        # TODO: Ensure that we can't create duplicate content
        content_type = ExternalContentType.objects.get(slug=instagram_obj.get('type'))
        new_content, _ = ExternalContent.objects.get_or_create(
            original_id=instagram_obj.get('originalId'),
            content_type=content_type,
            text_content=instagram_obj.get('textContent'),
            image_url=instagram_obj.get('imageUrl'))
        new_content.tagged_products.add(product)
        new_content.save()

    messages.success(request, 'Successfully tagged {0} content items with "{1}"'
        .format(len(instagram_content), product.name))

    return redirect('asset-manager', store_id=store_id)


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
                                             context, request=request)
    else:
        return render_to_response('pinpoint/campaign.html', arguments,
                                  context_instance=context)


def generate_static_campaign(campaign, contents, force=False):
    """write a PinPoint page to local storage.

    returns whether the file was written.
    """
    write = False
    filename = '%s/static/pinpoint/html/%s.html' % (os.path.dirname(
        os.path.realpath(__file__)), campaign.id)
    # the "robust" file exists method: stackoverflow.com/a/85237
    try:
        with file(filename) as tf:
            if force:
                write = True
    except IOError:
        write = True

    if write:
        with file(filename, 'w') as tf2:
            tf2.write(contents)

    return write


def save_static_campaign(campaign, contents, force=False):
    # does not expire.
    filename = '%s.html' % campaign.id
    try:
        storage = S3BotoStorage(bucket='campaigns.secondfunnel.com',
                                access_key=settings.AWS_ACCESS_KEY_ID,
                                secret_key=settings.AWS_SECRET_ACCESS_KEY)

        thing = storage.open(filename, 'w')
        thing.write(contents)
        thing.close()
    except IOError, err:
        # storage is not available. bring attention if it was forced
        if force:
            raise IOError(err)


def campaign_to_theme_to_response(campaign, arguments, context=None,
                                  request=None):
    """Generates the HTML page for a standard pinpoint product page.

    Related products are populated statically only if a request object
    is provided.
    """
    if not context:
        context = Context()
    context.update(arguments)

    related_results = []

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

    if request:
        # "borrow" IR for results
        related_results = get_seeds(request, store=campaign.store.slug,
                                    campaign=campaign.id,
                                    seeds=product.id,
                                    results=100,
                                    raw=True)
    context.update({
        'product': product,
        'campaign': campaign,
        'backup_results': related_results,
        'random_results': related_results,
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
            result = actions.get(type, noop)(value)

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
    rendered_page = page.render(context)
    if not settings.DEBUG:
        written = generate_static_campaign(campaign, rendered_page, force=False)
        save_static_campaign(campaign, rendered_page, force=written)

    return HttpResponse(rendered_page)


def app_exception_handler(request):
    import sys, traceback

    type, exception, tb = sys.exc_info()
    stack = traceback.format_exc().splitlines()

    return HttpResponseServerError(loader.get_template('500.html').render(
        Context({'exception': exception,
                 'traceback': '\n'.join(stack)})))