from django.views.decorators.csrf import csrf_exempt

from apps.api.decorators import check_login, request_methods
from apps.intentrank.utils import ajax_jsonp
from apps.static_pages.views import (generate_static_campaign,
                                     transfer_static_campaign)


@check_login
@csrf_exempt
@request_methods('POST', 'PUT', 'PATCH')
def generate_static_page(request, store_id, page_id):
    """alias"""
    return generate_static_campaign(request, store_id, campaign_id=page_id)


# @check_login
# @csrf_exempt
# @request_methods('POST', 'PUT', 'PATCH')
def transfer_static_page(request, store_id, page_id):
    i = transfer_static_campaign(store_id, page_id)

    # could have 500'd otherwise
    return ajax_jsonp({"successful": i})
