from apps.intentrank.utils import ajax_jsonp
from apps.pinpoint.models import Campaign, Store
from apps.static_pages.tasks import generate_static_campaign

def regenerate_static_campaign(request, campaign_id):
    """Manual stimulation handler: re-save a campaign.

    Campaign *will* be regenerated despite having a static log entry.

    @param [{string}] callback: jsonp callback (defaults to "callback")
    @returns {jsonp} true if succeeded, false if failed, null if campaign not found
    """
    result = None
    try:
        result = Campaign.objects.get(pk=campaign_id)

        generate_static_campaign.delay(campaign_id, ignore_static_logs=True)
        result = True  # succeeded
    except Campaign.DoesNotExist:
        pass
    except:
        result = False  # for other reasons... failed

    # the return is either null, or true
    return ajax_jsonp(result, request.GET.get('callback', 'callback'))