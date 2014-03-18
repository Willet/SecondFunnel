import collections
import json
from django import http
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView
from tastypie.exceptions import BadRequest
from tastypie.paginator import Paginator
from apps.api.decorators import request_methods, check_login
from apps.assets.models import BaseModel
from apps.intentrank.utils import returns_cg_json, ajax_jsonp


class ContentGraphPaginator(Paginator):
    def __init__(self, *args, **kwargs):
        kwargs.pop('collection_name')
        super(ContentGraphPaginator, self).__init__(*args, **kwargs)

    def get_limit(self):
        """Changes the 'results' (CG) param to 'limit'"""
        limit = self.request_data.get('results', self.request_data.get(
            'limit', self.limit))
        if limit is None:
            limit = getattr(settings, 'API_LIMIT_PER_PAGE', 20)

        try:
            limit = int(limit)
        except ValueError:
            raise BadRequest("Invalid limit '%s' provided. Please provide a positive integer." % limit)

        if limit < 0:
            raise BadRequest("Invalid limit '%s' provided. Please provide a positive integer >= 0." % limit)

        if self.max_limit and (not limit or limit > self.max_limit):
            # If it's more than the max, we're only going to return the max.
            # This is to prevent excessive DB (or other) load.
            return self.max_limit

        return limit

    def page(self):
        output = super(ContentGraphPaginator, self).page()

        output['results'] = output['objects']

        meta = output['meta']
        output['meta'] = {
            'cursors': {
                # no previous offset was provided by CG
                'next': meta['offset'] + len(output['results'])
            }
        }

        return output


class JSONResponseMixin(object):
    def render_to_response(self, context):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        return http.HttpResponse(content,
                                 content_type='application/json',
                                 **httpresponse_kwargs)

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return json.dumps(context)


def cg_endpoint(fn):
    """Repetitive shorthand for common decorators applied to CG handlers.
    You don't have to use this.

    """
    @request_methods('GET', 'POST', 'PATCH', 'DELETE')
    @check_login
    @never_cache
    @csrf_exempt
    @returns_cg_json
    def wrapped(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapped


class BaseCGHandler(JSONResponseMixin, ListView):
    """Making REST APIs is a legit use of CBV, right?"""
    model = BaseModel
    page_kwarg = 'offset'

    @method_decorator(never_cache)
    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """decides if this is a GET/POST/...
        Currently being exploited to set initial values.
        """
        request = args[0]
        try:  # try overwritten method signature (if present)
            self.object_list = self.get_queryset(request=request)
        except:
            self.object_list = self.get_queryset()

        self.paginate_by = request.GET.get('results', settings.API_LIMIT_PER_PAGE)
        return super(BaseCGHandler, self).dispatch(*args, **kwargs)

    def get_paginate_by(self, queryset):
        """return None for no pagination.

        :returns {int}
        """
        try:
            return self.paginate_by or settings.API_LIMIT_PER_PAGE
        except AttributeError:
            return settings.API_LIMIT_PER_PAGE

    def get_allow_empty(self):
        return True

    def serialize(self, things=None):
        if not things:
            things = self.object_list

        # multiple objects (paginate)
        if isinstance(things, collections.Iterable) and type(things) != dict:
            paginator, page, queryset, is_paginated = self.paginate_queryset(
                things, self.get_paginate_by(things))

            result_set = [obj.to_cg_json() for obj in page.object_list]
            if page.has_next():
                return {
                    'results': result_set,
                    'meta': {
                        'cursor': {
                            'next': page.next_page_number(),
                        },
                    },
                }
            else:
                return {
                    'results': result_set,
                }
        # single object
        return things.to_cg_json()

    def get(self, request, *args, **kwargs):
        return ajax_jsonp(self.serialize())

    def post(self, request, *args, **kwargs):
        """default POST behaviour: apply whichever object attributes
        you supply as the body and save the object.
        """
        data = json.loads(request.body)
        new_object = self.model()
        new_object.update(**data)
        if isinstance(kwargs.get('obj_attrs'), dict):
            new_object.update(**kwargs.get('obj_attrs'))

        new_object.save()  # :raises ValidationError
        return ajax_jsonp(new_object.to_cg_json())

    def put(self, request, *args, **kwargs):
        raise NotImplementedError()

    def patch(self, request, *args, **kwargs):
        request = args[0]
        object = get_object_or_404(self.model, id=kwargs.get('object_id'))
        object.update(**json.loads(request.body))
        object.save()
        return ajax_jsonp(object.to_cg_json())

    def delete(self, request, *args, **kwargs):
        request = args[0]
        object = get_object_or_404(self.model, id=kwargs.get('object_id'))
        object.delete()
        return HttpResponse(status=200)
