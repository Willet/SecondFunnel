from apps.static_pages.utils import render_campaign

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login
from django.shortcuts import get_object_or_404, redirect
from django.template import Context, loader
from django.http import HttpResponse, HttpResponseServerError
from django.views.decorators.vary import vary_on_headers

from apps.pinpoint.models import Campaign


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
    campaign_instance = get_object_or_404(Campaign, pk=campaign_id)
    campaign_instance.live = False
    campaign_instance.save()

    messages.success(request, "Your page was deleted.")

    return redirect('store-admin', store_id=store_id)


@vary_on_headers('Accept-Encoding')
def campaign(request, store_id, campaign_id):
    """Returns a rendered campaign response of the given id."""
    rendered_content = render_campaign(store_id, campaign_id,
        request=request)

    return HttpResponse(rendered_content)


def app_exception_handler(request):
    """Renders the "something broke" page. JS console shows the error."""
    import sys, traceback

    _, exception, _ = sys.exc_info()
    stack = traceback.format_exc().splitlines()

    return HttpResponseServerError(loader.get_template('500.html').render(
        Context({'exception': exception,
                 'traceback': '\n'.join(stack)})))
