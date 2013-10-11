from urllib import urlencode
from apps.static_pages.utils import render_campaign
from django.db.models import Q
from apps.pinpoint.forms import ThemeForm

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404, redirect, render
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseServerError, HttpResponseNotAllowed
from fancy_cache import cache_page
from django.views.decorators.vary import vary_on_headers

from apps.assets.models import Store
from apps.intentrank.views import get_seeds

from apps.pinpoint.models import Campaign, BlockType, StoreTheme
from apps.pinpoint.decorators import belongs_to_store, has_store_feature
from apps.utils.ajax import ajax_error, ajax_success

import apps.utils.base62 as base62
from apps.utils.caching import nocache


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
@has_store_feature('pages')
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
    """
    First step in creating a new pinpoint page. Displays available block types,
    allowing user to select one and continue.

    @param request: The request for this page.
    @param store_id: The store to create a new page for.

    @return: An HttpResponse which renders the page template.
    """
    store = get_object_or_404(Store, pk=store_id)

    return render_to_response('pinpoint/admin_new_campaign.html', {
        "store": store,
        "block_types": BlockType.objects.all(),
    }, context_instance=RequestContext(request))


@login_required
def delete_campaign(request, store_id, campaign_id):
    campaign_instance = get_object_or_404(Campaign, pk=campaign_id)
    campaign_instance.live = False
    campaign_instance.save()

    messages.success(request, "Your page was deleted.")

    return redirect('store-admin', store_id=store_id)


@belongs_to_store
@has_store_feature('theme-manager')
@login_required
def theme_manager(request, store_id):
    """renders the page that allows store owners to view themes associated with
    their store or campaigns.
    """
    store = get_object_or_404(Store, pk=store_id)

    themes = set(StoreTheme.objects.filter(
        Q(store__id=store_id)
        | Q(store_mobile__id=store_id)
        | Q(theme__isnull=False)
        | Q(mobile__isnull=False)
    ))

    theme_list = []
    tag_map = {
        'store': ['Store Default'],
        'store_mobile': ['Store Default', 'Mobile'],
        'theme': ['Campaign'],
        'mobile': ['Campaign', 'Mobile']
    }
    for theme in themes:
        tags = []
        for key in ['store', 'store_mobile', 'theme', 'mobile']:
            try:
                if hasattr(theme, key):
                    tags.extend(tag_map[key])
            except:
                pass

            tags = list(set(tags))

        theme_list.append({
            'obj': theme,
            'tags': tags
        })

    return render_to_response('pinpoint/theme_manager.html', {
        "store": store,
        "store_id": store_id,
        "themes": theme_list
    }, context_instance=RequestContext(request))

@belongs_to_store
@login_required
def edit_theme(request, store_id, theme_id=None):
    """renders the page that allows store owners to edit themes or create new
     themes
    """
    store = get_object_or_404(Store, pk=store_id)

    try:
        theme = StoreTheme.objects.get(pk=theme_id)
    except StoreTheme.DoesNotExist:
        theme = None

    template_vars = {
        'store': store,
        'store_id': store_id,
        'theme_id': theme_id,
        'preview_enabled': True,
    }


    try:
        campaign = Campaign.objects.filter(store=store).order_by('-last_modified')[0]
    except IndexError:  # store has no campaigns
        # can't preview without an existing campaign
        template_vars.update({'preview_enabled': False})

    if request.method == 'GET' and theme:
        # Only have to do something if the theme already exists
        template_vars['formset'] = ThemeForm(instance=theme, store_id=store_id)
    elif request.method == 'POST':
        form = ThemeForm(request.POST, instance=theme, store_id=store_id)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                '"{0}" saved successfully.'.format(form.cleaned_data['name'])
            )
            return redirect('theme-manager', store_id=store_id)

        template_vars['formset'] = form
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

    return render_to_response(
        'pinpoint/theme_editor.html',
        template_vars,
        context_instance=RequestContext(request)
    )


@belongs_to_store
@login_required
def style_theme(request, store_id, theme_id):
    """Render live theme editor, and, if applicable, save the theme."""

    store = get_object_or_404(Store, pk=store_id)
    theme = get_object_or_404(StoreTheme, pk=theme_id)

    template_vars = {
        'store': store,
        'store_id': store_id,
        'theme_id': theme_id,
        'preview_enabled': True,
    }

    try:
        campaign = Campaign.objects.filter(store=store).order_by('-last_modified')[0]
    except IndexError:  # store has no campaigns
        messages.error(request, 'Cannot open the theme editor. '
            'Theme preview requires at least one campaign in your account.')
        return redirect('theme-manager', store_id=store_id)

    # fields we have substitution tables (and names) for
    themable_fields = [(".cell", "Featured product area"),
                       (".lifestyle.cell", "Shop-the-look area"),
                       (".block", "Generic block"),
                       (".product.block", "Product block"),
                       (".block.combobox", "Combobox"),
                       (".preview", "Preview area"),
                       (".preview.container .content .instagram",
                        "Instagram preview area")]

    if request.method == 'POST':
        style_map = {}
        for x in themable_fields:
            style_map[x[0]] = request.POST.get(x[0], '')
        theme.set_styles(style_map=style_map)
        theme.save()
        template_vars.update({'theme_saved': True})

    # response_body is used to scan for styling regions declared by the theme.
    response_body = render_campaign(campaign.id, request, get_seeds)
    field_styles = []
    for selector, hint in themable_fields:
        field_style = theme.get_styles(response_body, selector)
        field_styles.append({
            'selector': selector,
            'hint': hint,
            'styles': field_style
        })
    template_vars.update({'themable_fields': field_styles})

    return render_to_response(
        'pinpoint/theme_preview.html',
        template_vars,
        context_instance=RequestContext(request)
    )

@has_store_feature('theme-manager')
@belongs_to_store
@login_required
def preview_theme(request, store_id, theme_id=None):
    """Generates a dummy page based on the theme data the user supplies.

    @deprecated

    POST creates a dummy theme.
    GET generates a dummy page, then deletes the dummy theme.
    """
    store = get_object_or_404(Store, pk=store_id)
    dummy_theme_name = '(preview)'

    template_vars = {
        'store': store,
        'store_id': store_id,
        'theme_id': theme_id
    }

    try:
        campaign = Campaign.objects.filter(store=store).order_by('-last_modified')[0]
    except IndexError:  # store has no campaigns
        return ajax_error({
            'error': 'Theme preview requires at least one campaign in your account.'})

    # call this func, first with POST, then with GET, to bypass
    # chrome's xss ban
    if request.method == 'GET':
        # generate a campaign page using a dummy theme (campaign is not saved)
        theme_id = request.GET.get('dummy_theme_id') or theme_id
        theme = get_object_or_404(StoreTheme, pk=theme_id)

        campaign.theme = theme

        response_body = render_campaign(campaign.id, request, get_seeds)
        page = HttpResponse(response_body)

        if request.GET.get('dummy_theme_id'):  # delete only if made to mock
            theme.delete()  # remove temporary theme
        return page

    elif request.method == 'POST':
        theme = get_object_or_404(StoreTheme, pk=theme_id)
        theme.pk = None  # clone obj
        for key in request.POST:
            try:
                setattr(theme, key, request.POST[key])
            except:
                raise
        theme.save()  # create (temporary) theme

        return ajax_success({
            'nextUrl': '%s?dummy_theme_id=%s' % (
                reverse('preview-theme', args=(store_id, theme.pk)),
                theme.pk),
            'dummy_theme_id': theme.pk})


# campaigns with short URLs are cached for 30 minutes
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


@vary_on_headers('Accept-Encoding')
def campaign(request, store_id, campaign_id):
    """Returns a rendered campaign response of the given id."""
    rendered_content = render_campaign(store_id, campaign_id,
        request=request, get_seeds_func=get_seeds)

    return HttpResponse(rendered_content)


def app_exception_handler(request):
    """Renders the "something broke" page. JS console shows the error."""
    import sys, traceback

    _, exception, _ = sys.exc_info()
    stack = traceback.format_exc().splitlines()

    return HttpResponseServerError(loader.get_template('500.html').render(
        Context({'exception': exception,
                 'traceback': '\n'.join(stack)})))
