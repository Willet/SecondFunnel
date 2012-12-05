import json
import random
import datetime

from datetime import timedelta, datetime

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType

from apps.assets.models import Store
from apps.analytics.models import Category, Metric, KVStore
from apps.pinpoint.models import Campaign
from apps.utils.ajax import ajax_success, ajax_error


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


@login_required
def analytics_pinpoint(request):
    # one of these is required:
    campaign_id = request.GET.get('campaign_id', False)
    store_id = request.GET.get('store_id', False)
    object_id = store_id or campaign_id

    # only one must be present
    if (campaign_id and store_id) and not object_id:
        return ajax_error()

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        start_date = datetime.datetime(
            year=start_date.split("/")[0],
            month=start_date.split("/")[1],
            day=start_date.split("/")[2]
        )

    if end_date:
        end_date = datetime.datetime(
            year=end_date.split("/")[0],
            month=end_date.split("/")[1],
            day=end_date.split("/")[2]
        )

    # get a store associated with this request, or bail out
    store = None
    try:
        store = Store.objects.get(id=store_id)

    except Store.DoesNotExist:
        pass

    try:
        campaign = Campaign.objects.get(id=campaign_id)
        store = campaign.store

    except Campaign.DoesNotExist:
        pass

    if not store:
        return ajax_error()

    # check if user is authorized to access this data
    if not request.user in store.staff.all():
        return ajax_error()

    # get appropriate content type to look up data
    if campaign_id:
        object_type = ContentType.objects.get_for_model(Campaign)
    else:
        object_type = ContentType.objects.get_for_model(Store)

    # iterate through analytics structures and get the data
    results = {}
    for category in Category.objects.filter(enabled=True).all():
        results[category.name] = {}

        for metric in category.metrics.filter(enabled=True).all():

            # just get the KV's associated with this object
            data = metric.data.filter(
                content_type=object_type, object_id=object_id
            ).order_by('-timestamp')

            if start_date:
                data = data.filter(timestamp__gte=start_date)

            if end_date:
                data = data.filter(timestamp__lte=end_date)

            results[category.name][metric.slug] = {
                'totals': {},

                # this exposes daily data for each product
                'data': [
                    {
                        "id": datum.id,
                        "timestamp": datum.timestamp.date().isoformat(),
                        "value": int(datum.value),
                        "product_id": datum.target_id
                    }
                    for datum in data.all()
                ]
            }

            bucket = results[category.name][metric.slug]
            # this aggregates and exposes daily data across all products
            for datum in bucket['data']:
                if datum['timestamp'] in bucket['totals']:
                    bucket['totals'][datum['timestamp']] += datum['value']
                else:
                    bucket['totals'][datum['timestamp']] = datum['value']

    return ajax_success(results)
