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
    if (campaign_id and store_id) or not object_id:
        return ajax_error()

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        start_date = [int(d) for d in start_date.split("/")]

        start_date = datetime(
            year=start_date[0],
            month=start_date[1],
            day=start_date[2]
        )

    if end_date:
        end_date = [int(d) for d in end_date.split("/")]

        end_date = datetime(
            year=end_date[0],
            month=end_date[1],
            day=end_date[2]
        )

    # try get a store associated with this request,
    # either directly or via campaign
    store = None
    try:
        store = Store.objects.get(id=store_id)

    except Store.DoesNotExist:
        pass

    if not store:
        try:
            campaign = Campaign.objects.get(id=campaign_id)
            store = campaign.store

        except Campaign.DoesNotExist:
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
        results[category.slug] = {}

        for metric in category.metrics.filter(enabled=True).all():

            # just get the KV's associated with this object
            data = metric.data.filter(
                content_type=object_type, object_id=object_id
            ).order_by('-timestamp')

            if start_date:
                data = data.filter(timestamp__gte=start_date)

            if end_date:
                data = data.filter(timestamp__lte=end_date)

            # ensure we have something set here, even if user didn't do this
            if len(data) > 0:
                start_date = start_date or data[0].timestamp
                end_date = end_date or data[::-1][0].timestamp

            results[category.slug][metric.slug] = {
                'name': metric.name,
                'totals': {},

                # this exposes daily data for each product
                # it's a list comprehension
                'data': [{
                            "id": datum.id,
                            "date": datum.timestamp.date().isoformat(),
                            "value": int(datum.value),
                            "product_id": datum.target_id,
                            "meta": datum.meta
                        } for datum in data.all()]
            }

            # this aggregates and exposes daily data across all products
            bucket = results[category.slug][metric.slug]
            for datum in bucket['data']:
                if datum['date'] in bucket['totals']:
                    bucket['totals'][datum['date']] += datum['value']
                else:
                    bucket['totals'][datum['date']] = datum['value']

            # zero-out out missing dates
            if start_date and end_date:
                for date in daterange(start_date, end_date + timedelta(1)):
                    if not date.date().isoformat() in bucket['totals']:
                        bucket['totals'][date.date().isoformat()] = 0

            if bucket['totals']:
                bucket['totals']['all'] = sum(bucket['totals'].values())
            else:
                bucket['totals']['all'] = 0

    return ajax_success(results)
