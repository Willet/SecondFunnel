import json
import random
import datetime

from datetime import timedelta, datetime

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType

from apps.assets.models import Store
from apps.analytics.models import AnalyticsData
from apps.pinpoint.models import Campaign
from apps.utils.ajax import ajax_success, ajax_error


def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)


@login_required
def analytics_pinpoint(request):
    # one of these is required:
    campaign_id = request.GET.get('campaign_id')
    store_id = request.GET.get('store_id')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not store_id and not campaign_id:
        return ajax_error()

    store = None

    if store_id:
        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            pass

    # campaign_id is set instead
    else:
        try:
            campaign = Campaign.objects.get(id=campaign_id)
            store = campaign.store
        except Campaign.DoesNotExist:
            pass

    # none of the above got us the store. Bail out
    if not store:
        return ajax_error()

    # check if user is authorized to access this data
    if not request.user in store.staff.all():
        return ajax_error()

    if campaign_id:
        campaign_type = ContentType.objects.get_for_model(Campaign)
        analytics_data = AnalyticsData.objects.filter(content_type=campaign_type, object_id=campaign.id)
    else:
        store_type = ContentType.objects.get_for_model(Store)
        analytics_data = AnalyticsData.objects.filter(content_type=store_type, object_id=store.id)

    # data template of what we're going to return
    return_data = {
        "visits": 0,
        "interactions": {
            "total": 0,
            "clickthrough": 0,
            "open_popup": 0,
            "shares": {
                "featured": 0,
                "popup": 0
            }
        },

        "daily": {}
    }

    # calculate totals and set daily data points for this data set
    for data in analytics_data:
        isodate = data.date.isoformat()

        if not isodate in return_data['daily']:

            # daily data template
            return_data['daily'][isodate] = {
                'visits': 0,
                'interactions': {
                    'total': 0,
                    'clickthrough': 0,
                    'open_popup': 0,
                    'shares': {
                        'featured': 0,
                        'popup': 0
                    }
                }
            }

        if data.key == "visits":
            return_data['visits'] += data.value
            return_data['daily'][isodate]['visits'] = data.value

        if data.key in ["clickthrough", "open_popup"]:
            return_data['interactions'][data.key] += data.value
            return_data['interactions']['total'] += data.value

            return_data['daily'][isodate]['interactions'][data.key] = data.value

        if data.key in ["featured", "popup"]:
            return_data['interactions']['shares'][data.key] += data.value
            return_data['interactions']['total'] += data.value

            return_data['daily'][isodate]['interactions']['shares'][data.key] = data.value

    return ajax_success(return_data)


# def analytics_overview(request):
#     app_slug = request.GET.get("app_slug")

#     # if not app_slug:
#         # return ajax_error({"message": "Missing parameters"})

#     visits = random.randint(2000, 5000)
#     interactions = random.randint(700, 3000)
#     data = {
#         "visits": visits,
#         "interactions": {
#             "total": interactions,
#             "clickthrough": int(interactions * random.uniform(0.01, 0.25)),
#             "popup": int(interactions * random.uniform(0.01, 0.25)),
#             "shares": {
#                 "featured": int(interactions * random.uniform(0.01, 0.25)),
#                 "popup": int(interactions * random.uniform(0.01, 0.25))
#             }
#         },

#         "daily": []
#     }

#     for s_date in daterange(datetime(2012, 9, 1), datetime.now()):
#         data["daily"].append({
#             "date": s_date.strftime("%Y-%m-%d"),
#             "visits": int(visits * random.uniform(0.025, 0.04)),
#             "interactions": {
#                 "total": int(interactions * random.uniform(0.025, 0.04)),
#                 "clickthrough": int(interactions * random.uniform(0.00033, 0.0083)),
#                 "popup": int(interactions * random.uniform(0.00033, 0.0083)),
#                 "shares": {
#                     "featured": int(interactions * random.uniform(0.00033, 0.0083)),
#                     "popup": int(interactions * random.uniform(0.00033, 0.0083))
#                 }
#             }
#         })

#     return ajax_success(data)
