from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.api.decorators import check_login, request_methods
from apps.api.resources import ContentGraphClient
from apps.api.utils import mimic_response
from secondfunnel.errors import deprecated


@request_methods('DELETE')
@check_login
@never_cache
@csrf_exempt
@deprecated
def delete_scraper(request, store_id, scraper_name):
    return HttpResponse(staus=200)


@request_methods('GET')
@check_login
@never_cache
@csrf_exempt
def list_scrapers(request, store_id):
    r = ContentGraphClient.scraper.store(store_id).GET()
    return mimic_response(r)
