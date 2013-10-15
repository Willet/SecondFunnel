from apps.intentrank.utils import ajax_jsonp
from apps.assets.models import Store
from apps.pinpoint.models import Campaign
from apps.static_pages.tasks import (create_bucket_for_store,
                                     generate_static_campaign)


def regenerate_static_campaign(request, store_id, campaign_id):
    """Manual stimulation handler: re-save a campaign.

    Campaign *will* be regenerated despite having a static log entry.

    @param [{string}] callback: jsonp callback (defaults to "callback")
    @returns {jsonp} true if succeeded, false if failed, null if campaign not found
    """
    result = None
    try:
        create_bucket_for_store.delay(store_id)
        generate_static_campaign.delay(store_id, campaign_id,
                                       ignore_static_logs=True)

        result = True  # succeeded
    except Campaign.DoesNotExist, Store.DoesNotExist:
        pass
    except (Exception, BaseException), err:
        result = str(err.message)  # for other reasons... failed

    # the return is either null, or true
    return ajax_jsonp(result, request.GET.get('callback', 'callback'))