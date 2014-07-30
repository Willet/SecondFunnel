import importlib
import json
from django.conf import settings

from django.core import serializers
from algorithms import ir_generic
from apps.assets.models import Category
from apps.intentrank.algorithms import ir_generic, qs_for, ir_base


class IntentRank(object):
    """Consider this an engine. Initializing one of those will emulate
    behaviour of a Feed object.

    # Requirements
    # - client side "shown"
    # - product tiles
    # - content tiles
    # - video tiles
    """
    feed = None
    _algorithm = None

    def __init__(self, feed, algorithm=ir_generic):
        """
        :param {Feed} feed   a Feed object with products
        """
        self._algorithm = None  # pycharm
        self.feed = feed
        if not feed:
            raise ValueError("Feed must exist, and must contain one item")
        if algorithm:
            self.set_algorithm(algorithm=algorithm)

    def __getattr__(self, item):
        """retrieve a reference to an existing algorithm.

        example: ir_object.all(...) -> [...]
        """
        try:
            module = importlib.import_module('apps.intentrank.algorithms')
            alg = getattr(module, item)
        except (ImportError, AttributeError) as err:
            return None
        return alg

    def get_algorithm(self, algorithm_name):
        """Look up an algorithm by name, or ir_generic if not found."""
        if 'finite_by_' in algorithm_name:
            return self.ir_finite_by(algorithm_name[10:])

        if 'ordered_by_' in algorithm_name:
            return self.ir_ordered_by(algorithm_name[11:])

        algorithm = getattr(self, 'ir_' + algorithm_name)
        if algorithm:
            return algorithm

        # verbose fallback
        print "Algorithm 'ir_{0}' not found; using ir_generic instead.".format(
            algorithm_name)
        return self.ir_generic

    def set_algorithm(self, algorithm):
        self._algorithm = algorithm

    @property
    def algorithm(self):
        return self._algorithm

    @algorithm.setter
    def algorithm(self, algorithm):
        self._algorithm = algorithm

    def get_results(self, serialize_format='json', *args, **kwargs):
        """Loads results from the feed, selects some from them
        (given conditions), and transforms these results into the format
        requested.

        :param results: number of results to return.

        :returns {*}
        """
        results = self._algorithm(self.feed, *args, **kwargs)
        return self.transform(results, serialize_format=serialize_format)

    def render(self, algorithm, *args, **kwargs):
        """View-like alias"""
        return self.transform(algorithm(*args, **kwargs))

    def transform(self, things, serialize_format='json'):
        """Virtual-repr() the thing using whichever serialization method
        makes sense.
        """
        new_things = []
        if serialize_format == 'json':
            for thing in things:
                # whatever it is, if it has a custom to_json method, use it
                if hasattr(thing, 'to_json'):
                    new_things.append(thing.to_json())  # raises on purpose
                    continue

                # whatever it is, if the default serializer works, also use it
                try:
                    new_things.append(serializers.serialize('json', thing))
                    continue
                except TypeError as err:
                    pass

                # if no custom method is found, dumps it directly (will raise)
                new_things.append(json.dumps(thing))
            return new_things
        elif serialize_format == 'raw':
            return things

        raise ValueError("Unknown format {0}".format(serialize_format))


def get_results(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                algorithm=ir_generic, tile_id=0, offset=0, **kwargs):
    """Converts a feed into a list of <any> using given parameters.

    :param feed        a <Feed>
    :param results     number of <any> to return
    :param exclude_set IDs of items in the feed to never consider
    :param request     (relay)
    :param algorithm   reference to a <Feed> => [<Tile>] function
    :param tile_id     for getting related tiles

    :returns           a list of <any>
    """
    if not feed.tiles.count():  # short circuit: return empty resultset
        return qs_for([])

    ir = IntentRank(feed=feed)

    # "everything except these tile ids"
    exclude_set = kwargs.get('exclude_set', [])
    request = kwargs.get('request', None)
    category_name = kwargs.get('category_name', None)
    if category_name:
        category = Category.objects.get(name=category_name)
        products = category.products.all()
        allowed_set = []
        for product in products:
            allowed_set += [t.id for t in product.tiles.all()]
            contents = product.content.all()
            for content in contents:
                allowed_set += [tile.id for tile in content.tiles.all()]
        allowed_set = list(set(allowed_set))
    else:
        allowed_set = None

    tiles = ir_base(feed=feed, allowed_set=allowed_set)
    args = dict(
        tiles=tiles, results=results,
        exclude_set=exclude_set, allowed_set=allowed_set,
        request=request, offset=offset, tile_id=tile_id, feed=feed)

    if 'products_only' in kwargs:
        args['products_only'] = kwargs.get('products_only')
    if 'content_only' in kwargs:
        args['content_only'] = kwargs.get('content_only')

    return algorithm(**args)
