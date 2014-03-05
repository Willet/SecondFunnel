try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError
from django.http.response import HttpResponseNotFound
from django.shortcuts import redirect
from django.template import Context, loader
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

from apps.assets.models import Page
from apps.pinpoint.utils import render_campaign


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


@cache_page(60 * 60 * 24, key_prefix="pinpoint-")  # 24 hours
@vary_on_headers('Accept-Encoding')
def campaign(request, store_id, page_id, mode=None):
    """Returns a rendered campaign response of the given id.

    :param mode   e.g. 'mobile' for the mobile page. Currently not functional.
    """
    rendered_content = render_campaign(store_id, page_id=page_id,
        request=request)

    return HttpResponse(rendered_content)


def campaign_by_slug(request, page_slug):
    """Used to render a page using only its name.

    If two pages have the same name (which was possible in CG), then django
    decides which page to render.
    """
    #page = get_object_or_404(Page, url_slug=page_slug)  # why doesn't this work?
    try:
        page = Page.objects.get(url_slug=page_slug)
    except Page.DoesNotExist:
        return HttpResponseNotFound()

    store_id = page.store_id
    return campaign(request, store_id=store_id, page_id=page.old_id)


def generate_static_campaign(request, store_id, page_id):
    """Too much confusion over the endpoint. Create alias for

    /pinpoint/id/id/regenerate == /static_pages/id/id/regenerate
    """
    from apps.static_pages.views import generate_static_campaign as real_gsc
    return real_gsc(request=request, store_id=store_id, page_id=page_id)


def app_exception_handler(request):
    """Renders the "something broke" page. JS console shows the error."""
    import sys, traceback

    _, exception, _ = sys.exc_info()
    stack = traceback.format_exc().splitlines()

    return HttpResponseServerError(loader.get_template('500.html').render(
        Context({'exception': exception,
                 'traceback': '\n'.join(stack)})))
