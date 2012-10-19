from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import Http404

from apps.pinpoint.models import Campaign
from apps.assets.models import Store


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
def new_campaign(request):

    return render_to_response('pinpoint/admin_new_campaign.html', {
        "store": store
    }, context_instance=RequestContext(request))


@login_required
def campaign_analytics_admin(request, campaign_id):
    pass


@login_required
def store_analytics_admin(request, store_id):
    pass


def campaign(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)

    return render_to_response('pinpoint/campaign.html', {
        "campaign": campaign
    }, context_instance=RequestContext(request))
