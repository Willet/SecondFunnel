import math
import json

from django.db.models import Count
from django.http import HttpResponse

from apps.assets.models import Product, Store

DEFAULT_RESULTS  = 12
MAX_BLOCKS_BEFORE_VIDEO = 50

class VideoCookie(object):
    def __init__(self):
        self.blocks_since_last = 0
        self.videos_already_shown = []

    def add_video(self, video_id):
        self.videos_already_shown.append(video_id)
        self.blocks_since_last = 0
        return self

    def add_blocks(self, blocks):
        self.blocks_since_last += blocks
        return self

    def is_empty(self):
        return self.blocks_since_last == 0 \
           and self.videos_already_shown == []

    def __str__(self):
        return "{0}, {1}".format(
            str(self.blocks_since_last), str(self.videos_already_shown))


def video_probability_function(x, m):
    if x <= 0:
        return 0
    elif x >= m:
        return 1
    else:
        return 1 - (math.log(m - x) / math.log(m))

def random_products(store, param_dict, id_only=True):
    """Returns a list of random product ids, as would be returned by IR.

    Only used in development; not in production"""
    store_id = Store.objects.get(slug__exact=store)
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
    return HttpResponse("{0}({1});".format(callback_name,
                                           json.dumps(result,
                                                      ensure_ascii=False)),
        mimetype='application/json', status=status)
