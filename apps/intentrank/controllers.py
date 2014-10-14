import importlib
import json
from django.conf import settings
from django.core import serializers
from django.db.models import Q

from apps.assets.models import Category, Tile, Content
from apps.intentrank.algorithms import ir_generic, ir_finite_by, ir_ordered_by, \
    qs_for, ir_base


class IntentRank(object):
    """Logical ordering wrapper around a feed."""
    _feed = None
    _page = None
    _algorithm = None  # :type function
    _results = None  # pre-transform

    def __init__(self, feed=None, page=None):
        """
        :param {Feed} feed   a Feed object with products
        """
        if page:
            self._page = page
            self._feed = page.feed
        elif feed:
            self._feed = feed
            if feed.page.count():
                self._page = feed.page.all()[0]  # caution
        else:
            raise AttributeError("Must supply one or more of: feed, page")

    def _resolve_algorithm(self, algorithm_name):
        """Look up an algorithm by name, or None if not found.

        :returns {function|None}
        """
        if not algorithm_name.startswith('ir_'):  # normalize algo names
            algorithm_name = 'ir_{}'.format(algorithm_name)

        if 'finite_by_' in algorithm_name:
            return ir_finite_by(algorithm_name[13:])

        if 'ordered_by_' in algorithm_name:
            return ir_ordered_by(algorithm_name[14:])

        try:
            module = importlib.import_module('apps.intentrank.algorithms')
            algorithm = getattr(module, algorithm_name)
            return algorithm
        except (ImportError, AttributeError):
            pass

        print "Warning: algorithm '{}' not found".format(algorithm_name)
        return None

    def _get_algorithm(self, algorithm=None):
        """:returns function  algorithm with highest specificity."""
        if algorithm is None and self._algorithm:
            algorithm = self._algorithm

        if isinstance(algorithm, basestring):
            algorithm = self._resolve_algorithm(algorithm)

        if not algorithm and self._page and \
                self._page.theme_settings.get('feed_algorithm'):
            algorithm = self._resolve_algorithm(
                self._page.theme_settings.get('feed_algorithm'))
        if not algorithm and self._feed and \
                self._feed.feed_algorithm:
            algorithm = self._resolve_algorithm(
                self._feed.feed_algorithm)

        if not algorithm:
            algorithm = ir_generic
        return algorithm

    @property
    def algorithm(self):
        """Returns one algorithm in this order:

        - if this IntentRank object has one already determined, then that one
        - page's algo
        - feed's algo
        - ir_generic
        """
        return self._get_algorithm()

    @algorithm.setter
    def algorithm(self, algorithm):
        self._algorithm = self._get_algorithm(algorithm)

    def get_results(self, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                    algorithm=None, tile_id=0, offset=0, **kwargs):
        """Converts a feed into a list of <any> using given parameters.

        :param results     number of <any> to return
        :param exclude_set IDs of items in the feed to never consider
        :param request     (relay)
        :param algorithm   reference to a <Feed> => [<Tile>] function
        :param tile_id     for getting related tiles

        :returns           a list of <any>
        """
        # "everything except these tile ids"
        exclude_set = kwargs.get('exclude_set', [])
        request = kwargs.get('request', None)
        category_name = kwargs.get('category_name', None)
        feed = self._feed

        if not algorithm:
            algorithm = self.algorithm

        if not feed.tiles.count():  # short circuit: return empty resultset
            return qs_for([])

        try:
            if self._page:
                category = Category.objects.filter(store=self._page.store,
                                                   name=category_name)[0]
            else:
                category = Category.objects.filter(name=category_name)[0]
            products = category.products.all()
        except (IndexError, Category.DoesNotExist):
            category = None
            products = []

        if category_name and category:
            contents = Content.objects.filter(tagged_products__in=products)
            tiles = Tile.objects.filter(Q(products__in=products) | Q(content__in=contents)).values_list('id', flat=True).distinct()
            allowed_set = list(tiles)
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

    def to_json(self):
        """
        :returns list
        """
        new_things = []
        self._results = self._results or []
        for thing in self._results:
            # whatever it is, if it has a custom to_json method, use it
            if hasattr(thing, 'to_json'):
                new_things.append(thing.to_json())  # raises on purpose
                continue

            # whatever it is, if the default serializer works, also use it
            try:
                new_things.append(serializers.serialize('json', thing))
                continue
            except TypeError:
                pass

            # if no custom method is found, dumps it directly (will raise)
            new_things.append(json.dumps(thing))
        return new_things
