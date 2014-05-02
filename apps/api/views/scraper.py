from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.api.decorators import check_login, request_methods
from apps.api.resources import ContentGraphClient
from apps.api.utils import mimic_response


@request_methods('GET')
@check_login
@never_cache
@csrf_exempt
def list_scrapers(request, store_id):
    r = ContentGraphClient.scraper.store(store_id).GET()
    return mimic_response(r)
