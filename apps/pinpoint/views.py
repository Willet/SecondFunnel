from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from apps.pinpoint.models import Campaign


def campaign(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)

    return render_to_response('pinpoint/campaign.html', {
        "campaign": campaign
    }, context_instance=RequestContext(request))
