import json
from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from apps.api.decorators import request_methods, check_login
from apps.assets.models import Store
from apps.intentrank.utils import returns_cg_json


@request_methods('GET', 'POST', 'PATCH', 'DELETE')
@check_login
@never_cache
@csrf_exempt
@returns_cg_json
def handle_store(request, store_id=0, offset=1,
                   results=settings.API_LIMIT_PER_PAGE, obj_attrs=None):
    """Implements the following API patterns:

    GET /store
    GET /store/id
    POST /store
    PATCH /store/id
    DELETE /store/id
    """
    if store_id:
        try:
            store = [Store.objects.filter(old_id=store_id)[0]]
        except IndexError:
            raise Http404()
    else:
        store = Store.objects.all()

    if not offset:
        offset = 1
    paginator = Paginator(store, results)
    page = paginator.page(offset)
    next_ptr = page.next_page_number() if page.has_next() else None

    # GET /store/id
    if request.method == 'GET' and store_id:
        return page.object_list[0].to_cg_json()
    # GET /store/id
    elif request.method == 'GET':
        return [c.to_cg_json() for c in page.object_list], next_ptr
    # POST /store
    elif request.method == 'POST':
        attrs = json.loads(request.body)
        new_store = Store()
        new_store.update(**attrs)
        if obj_attrs:
            new_store.update(**obj_attrs)
        new_store.save()  # :raises ValidationError
        return new_store.to_cg_json()
    # PATCH /store/id
    elif request.method == 'PATCH' and store_id:
        store = store[0]
        store.update(**json.loads(request.body))
        if obj_attrs:
            store.update(**obj_attrs)
        store.save()  # :raises ValidationError
        return store.to_cg_json()
    # DELETE /store/id
    elif request.method == 'DELETE':
        store = store[0]
        store.delete()
        return HttpResponse(status=200)  # it would be 500 if delete failed


