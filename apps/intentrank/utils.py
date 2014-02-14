import json

from django.db.models import Q
from django.http import HttpResponse

from apps.assets.models import Product, Store, BaseModelNamed

DEFAULT_RESULTS = 12


def random_products(store_slug, param_dict, id_only=True):
    """Returns a list of random product ids, as would be returned by IR.

    Only used in development; not in production"""
    store_id = Store.objects.filter(Q(slug=store_slug) | Q(name=store_slug))
    num_results = int(param_dict.get('results', DEFAULT_RESULTS))
    results = []
    iters = 0  # prevent infinite loop when DB has no products

    while len(results) < num_results and iters < 50:
        query_set = Product.objects.select_related()\
                           .filter(store_id__exact=store_id)[:num_results]
        results_partial = list(query_set)

        if id_only:
            results_partial = [x.id for x in results_partial]

        results.extend(results_partial)
        iters = iters + 1

    return results[:num_results]


def ajax_jsonp(result, callback_name=None, status=200):
    """
    This function now serves JSON as well as JSONP, when callback_name is None.

    @param result   a json-serializable object, or an object that
                    has a json() method.
    @param callback_name  a callback. if omitted, json.
                                      if '', 'callback'.
    """
    def serialize(result):
        response_text = ''

        if isinstance(result, (bool, int, float, str, basestring)):
            response_text = json.dumps(result)
        elif isinstance(result, BaseModelNamed):
            response_text = result.json()
        elif isinstance(result, (tuple, list)):
            result_list = []
            for r in result:
                result_list.append(json.loads(serialize(r)))
            response_text = json.dumps(result_list)
        elif isinstance(result, dict):
            result_list = {}
            for r in result:
                result_list[r] = json.loads(serialize(result[r]))
            response_text = json.dumps(result_list)
        else:
            try:
                response_text = json.dumps(result)
            except TypeError:
                raise  # no serialization method worked
        return response_text

    response_text = serialize(result)

    if callback_name == '':
        callback_name = 'callback'

    if callback_name:
        return HttpResponse("{0}({1});".format(callback_name, response_text),
                            content_type='application/javascript', status=status)
    else:
        return HttpResponse(response_text,
                            content_type='application/json', status=status)
