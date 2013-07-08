"""Ajax (read-only) interface for analytics data."""
from collections import defaultdict
from datetime import timedelta, datetime

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType

from apps.assets.models import Store
from apps.analytics.models import Category, CategoryHasMetric
from apps.pinpoint.decorators import belongs_to_store
from apps.pinpoint.models import Campaign, IntentRankCampaign
from apps.utils.ajax import ajax_success, ajax_error


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

# @belongs_to_store (does not supply store_id in this manner)
@login_required
def analytics_pinpoint(request):
    """Aggregates analytics data found in the DB, and returns
    aggregate values.

    @param request: django request handler
    """
    def aggregate_by(metric_slug, bucket, key):
        """Generates a dictionary that contains data tallies."""
        bucket['totals'][key] = defaultdict(int)

        for datum in bucket['data']:
            if metric_slug == "awareness-bounce_rate":
                # rates are fractions and shouldn't be summed
                bucket['totals'][key][datum[key]] = datum['value']
            else:
                bucket['totals'][key][datum[key]] += datum['value']

        if key == 'date':
            # zero-out out missing dates
            if start_date and end_date:
                for date in daterange(start_date, end_date + timedelta(days=1)):
                    if not date.date().isoformat() in bucket['totals'][key]:
                        bucket['totals'][key][date.date().isoformat()] = 0

        if bucket['totals'][key]:
            bucket['totals'][key]['all'] = sum(bucket['totals'][key].values())
        else:
            bucket['totals'][key]['all'] = 0

    # one of these is required:
    campaign_id = request.GET.get('campaign_id', False)
    store_id = request.GET.get('store_id', False)
    if (campaign_id and store_id) or (not store_id and not campaign_id):
        return ajax_error({'error': 'campaign_id or store_id must be present'})

    # try get a store associated with this request,
    # either directly or via campaign
    if store_id:
        store = Store.objects.get(id=store_id)
        campaign = store.campaign_set.all().order_by("-created")[0]

    elif campaign_id:
        try:
            campaign = IntentRankCampaign.objects.get(id=campaign_id)

            # Since it's a M2M rel'n, even though we never associate
            # categories with other stores, we need to look through all of
            # the related campaigns and pick the *only* result
            store = campaign.campaigns.all()[0].store
        except IntentRankCampaign.DoesNotExist, err:
            return ajax_error(
                {'error': 'IntentRankCampaign %s not found' % campaign_id})

    date_range = request.GET.get('range', 'total')
    end_date = datetime.now()
    end_date = end_date.replace(tzinfo=campaign.created.tzinfo)

    if date_range == "total":  # since the beginning of collection
        start_date = campaign.created

    elif date_range == "month":
        start_date = end_date - timedelta(weeks=4)

    elif date_range == "two_weeks":
        start_date = end_date - timedelta(weeks=2)

    elif date_range == "week":
        start_date = end_date - timedelta(weeks=1)

    else:
        start_date = end_date - timedelta(days=1)

    start_date  = min(start_date, campaign.created)

    # account for potential timezone differences
    start_date = start_date - timedelta(days=2)

    # what to filter kv for
    object_type = ContentType.objects.get_for_model(Campaign)

    # iterate through analytics structures and get the data
    results = {}
    for category in Category.objects.filter(enabled=True):
        # categories: e.g. Awareness, Engagement, Sharing. In DB.
        results[category.slug] = {}

        for metric in category.metrics.filter(enabled=True):
            category_has_metric = CategoryHasMetric.objects.get(
                category=category, metric=metric)

            # get the KVs associated with this object
            data = metric.data.filter(
                content_type=object_type, object_id=campaign.id,
                timestamp__lte=end_date, timestamp__gte=start_date
            ).order_by('-timestamp')

            # ensure we have something set here, even if user didn't do this
            # TODO: this statement seems to have no effect
            if len(data) > 0:
                start_date = start_date or data[0].timestamp
                end_date = end_date or data[::-1][0].timestamp

            # this exposes daily data for each product in the right format
            formatted_data = []
            for datum in data.all():
                formatted_data.append({
                        "id": datum.id,
                        "date": datum.timestamp.date().isoformat(),
                        "value": int(datum.value),
                        "target_id": datum.target_id,
                        "meta": datum.meta
                    })

            results[category.slug][metric.slug] = {
                'name': metric.name,
                'order': category_has_metric.order,
                'display': category_has_metric.display,
                'totals': {'date': {}, 'target_id': {}, 'meta': {}},

                # this exposes daily data for each product
                'data': formatted_data
            }

            # this aggregates and exposes daily data across all products
            bucket = results[category.slug][metric.slug]
            aggregate_by(metric.slug, bucket, 'date')  # mutable
            aggregate_by(metric.slug, bucket, 'target_id')  # mutable
            aggregate_by(metric.slug, bucket, 'meta')  # mutable

    return ajax_success(results)
