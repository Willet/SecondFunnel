from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from apps.api.decorators import check_login
from apps.api.resources import ContentGraphClient
from apps.api.utils import mimic_response


@require_GET
@check_login
@never_cache
@csrf_exempt
def list_scrapers(request, store_id):
    r = ContentGraphClient.scraper.store(store_id).GET()
    return mimic_response(r)
