import json
import random
import datetime

from datetime import timedelta, datetime

from django.http import HttpResponse

from apps.utils.ajax import ajax_success


def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)


def analytics_overview(request):
    app_slug = request.GET.get("app_slug")

    # if not app_slug:
        # return ajax_error({"message": "Missing parameters"})

    visits = random.randint(2000, 5000)
    interactions = random.randint(700, 3000)
    data = {
        "visits": visits,
        "interactions": {
            "total": interactions,
            "clickthrough": int(interactions * random.uniform(0.01, 0.25)),
            "popup": int(interactions * random.uniform(0.01, 0.25)),
            "shares": {
                "featured": int(interactions * random.uniform(0.01, 0.25)),
                "popup": int(interactions * random.uniform(0.01, 0.25))
            }
        },

        "daily": []
    }

    for s_date in daterange(datetime(2012, 9, 1), datetime.now()):
        data["daily"].append({
            "date": s_date.strftime("%Y-%m-%d"),
            "visits": int(visits * random.uniform(0.025, 0.04)),
            "interactions": {
                "total": int(interactions * random.uniform(0.025, 0.04)),
                "clickthrough": int(interactions * random.uniform(0.00033, 0.0083)),
                "popup": int(interactions * random.uniform(0.00033, 0.0083)),
                "shares": {
                    "featured": int(interactions * random.uniform(0.00033, 0.0083)),
                    "popup": int(interactions * random.uniform(0.00033, 0.0083))
                }
            }
        })

    return ajax_success(data)
