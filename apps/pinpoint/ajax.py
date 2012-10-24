import json
import random
import datetime

from datetime import timedelta, datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from apps.pinpoint.models import Campaign
from apps.utils.ajax import ajax_success, ajax_error


@login_required
def campaign_save_draft(request):
    return modify_campaign(request, False)


@login_required
def campaign_publish(request):
    return modify_campaign(request, True)


def modify_campaign(request, enabled):
    if not request.method == 'POST':
        return ajax_error()

    campaign_id = request.POST.get('campaign_id')
    if not campaign_id:
        return ajax_error()

    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except:
        return ajax_error()
    else:
        if not request.user in campaign.store.staff.all():
            return ajax_error()

        campaign.enabled = enabled
        campaign.save()

    return ajax_success()
