import math
import json

from django.db.models import Count, Q
from django.http import HttpResponse

from apps.assets.models import Product, Store

DEFAULT_RESULTS  = 12


def random_products(store_slug, param_dict, id_only=True):
    """Returns a list of random product ids, as would be returned by IR.

    Only used in development; not in production"""
    store_id = Store.objects.filter(Q(slug=store_slug) | Q(name=store_slug))
    num_results = int(param_dict.get('results', DEFAULT_RESULTS))
    results = []

    while len(results) < num_results:
        query_set = Product.objects.select_related()\
                           .prefetch_related('lifestyleImages')\
                           .annotate(num_images=Count('media'))\
                           .filter(store_id__exact=store_id,
                                   num_images__gt=0)[:num_results]
        results_partial = list(query_set)

        if id_only:
            results_partial = [x.id for x in results_partial]

        results.extend(results_partial)

    return results[:num_results]

def ajax_jsonp(result, callback_name, status=200):
    response_text = ''
    try:
        response_text = json.dumps(result)
    except TypeError:  # blah blah is not JSON serializable
        try:
            # serialize BasedModelNamed objects
            response_text = result.json()
        except AttributeError:
            raise  # no serialization method worked
    pass

    return HttpResponse("{0}({1});".format(callback_name, response_text),
        mimetype='application/json', status=status)
