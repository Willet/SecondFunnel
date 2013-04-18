from urllib import urlencode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseServerError
from django.contrib.contenttypes.models import ContentType
from fancy_cache import cache_page
from social_auth.db.django_models import UserSocialAuth

from apps.analytics.models import Category
from apps.assets.models import ExternalContent, ExternalContentType, Store
from apps.intentrank.views import get_seeds

from apps.pinpoint.models import Campaign, BlockType
from apps.pinpoint.decorators import belongs_to_store
from apps.pinpoint.utils import render_campaign
import apps.pinpoint.wizards as wizards

import apps.utils.base62 as base62
from apps.utils.caching import nocache

from apps.utils.image_service.api import queue_processing
from apps.utils.social.utils import get_adapter_class


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


def login_success_redirect(request):
    """Redirects user to store admin page if he/she already logged in
    and attempts to log in again.
    """
    if request.user.is_authenticated():
        return login_redirect(request)
    else:
        return login(request)


@login_required
def social_auth_redirect(request):
    """
    Redirect after some social-auth action (association, or disconnection).

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

    accounts = []
    xcontent_types = ExternalContentType.objects.filter(enabled=True)
    for xcontent_type in xcontent_types:
        try:
            account_user = store.social_auth.get(provider=xcontent_type.slug)
        except UserSocialAuth.DoesNotExist:
            account_user = None

        if not account_user:
            try:
                account_user = user.social_auth.get(provider=xcontent_type.slug)
            except UserSocialAuth.DoesNotExist:
                account_user = None

        # Add the account regardless of if we have a user or not
        # We use this to determine which accounts to show
        accounts.append({
            'type': xcontent_type.slug,
            'connected': account_user,
            'data': getattr(account_user, 'extra_data', {})
        })

        # If we do have an account, start fetching content
        if account_user:
            cls = get_adapter_class(xcontent_type.classname)

            # If we can't get an adapter class, don't try to load content
            if not cls:
                continue

            adapter = cls(tokens=account_user.tokens)
            contents = adapter.get_content(count=500)

            for obj in contents:
                content_type = ExternalContentType.objects.get(slug=obj.get('type'))

                new_content, created = ExternalContent.objects.get_or_create(
                    store=store,
                    original_id=obj.get('original_id'),
                    content_type=content_type)

                if created:
                    new_content.text_content = obj.get('text_content')

                    new_image_url = queue_processing(
                        obj.get('image_url'),
                        store_slug=store.slug,
                        image_type=obj.get('type')
                    )

                    # imageservice might or might not be working today,
                    # so lets be careful with it
                    if new_image_url:
                        new_content.image_url = new_image_url

                # Any fields that should be periodically updated
                new_content.original_url=obj.get('original_url')
                new_content.username=obj.get('username')
                new_content.likes = obj.get('likes')
                new_content.user_image = obj.get('user-image')
                new_content.save()

    all_contents = store.external_content.all()

    return render_to_response('pinpoint/asset_manager.html', {
        "store": store,
        "accounts": accounts,
        "content": [
            ("Needs Review", "needs_review",
                all_contents.filter(approved=False, active=True)),
            ("Rejected", "rejected",
                all_contents.filter(active=False)),
            ("Approved", "approved",
                all_contents.filter(approved=True, active=True))
        ],
        "store_id": store_id
    }, context_instance=RequestContext(request))


# origin: campaigns with short URLs are cached for 30 minutes
@cache_page(60 * 30, key_prefix=nocache)
def campaign_short(request, campaign_id_short):
    """base62() is a custom function, so to figure out the long
    campaign URL, go to http://elenzil.com/esoterica/baseConversion.html
    and decode with the base in utils/base62.py.

    The long URL is (currently) /pinpoint/(long ID).
    """

    campaign_id = base62.decode(campaign_id_short)

    if any(x in request.GET for x in ['dev', 'unshorten']):
        response = redirect('campaign', campaign_id=campaign_id)
        response['Location'] += '?{0}'.format(urlencode(request.GET))
        return response

    return campaign(request, campaign_id)


def campaign(request, campaign_id):
    campaign_instance = get_object_or_404(Campaign, pk=campaign_id)
    mode = request.GET.get('mode', 'full')

    rendered_content = render_campaign(campaign_instance,
        request=request, get_seeds_func=get_seeds, mode=mode)

    return HttpResponse(rendered_content)


def app_exception_handler(request):
    """Renders the "something broke" page. JS console shows the error."""
    import sys, traceback

    _, exception, _ = sys.exc_info()
    stack = traceback.format_exc().splitlines()

    return HttpResponseServerError(loader.get_template('500.html').render(
        Context({'exception': exception,
                 'traceback': '\n'.join(stack)})))
