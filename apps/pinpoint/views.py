from django.views.decorators.cache import cache_page
from apps.assets.models import Page
from apps.static_pages.utils import render_campaign

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login
from django.shortcuts import get_object_or_404, redirect
from django.template import Context, loader
from django.http import HttpResponse, HttpResponseServerError
from django.views.decorators.vary import vary_on_headers


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
def delete_campaign(request, store_id, campaign_id):
    campaign_instance = get_object_or_404(Page, pk=campaign_id)
    campaign_instance.live = False
    campaign_instance.save()

    messages.success(request, "Your page was deleted.")

    return redirect('store-admin', store_id=store_id)


@cache_page(10000, key_prefix="pinpoint-")
@vary_on_headers('Accept-Encoding')
def campaign(request, store_id, campaign_id, mode=None):
    """Returns a rendered campaign response of the given id.

    :param mode   e.g. 'mobile' for the mobile page. Currently not functional.
    """
    rendered_content = render_campaign(store_id, campaign_id,
        request=request)

    return HttpResponse(rendered_content)


def generate_static_campaign(request, store_id, campaign_id):
    """Too much confusion over the endpoint. Create alias for

    /pinpoint/id/id/regenerate == /static_pages/id/id/regenerate
    """
    from apps.static_pages.views import generate_static_campaign as real_gsc
    return real_gsc(request=request, store_id=store_id, campaign_id=campaign_id)


def app_exception_handler(request):
    """Renders the "something broke" page. JS console shows the error."""
    import sys, traceback

    _, exception, _ = sys.exc_info()
    stack = traceback.format_exc().splitlines()

    return HttpResponseServerError(loader.get_template('500.html').render(
        Context({'exception': exception,
                 'traceback': '\n'.join(stack)})))
