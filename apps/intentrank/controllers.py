import importlib
import json

from django.conf import settings
from django.core import serializers
from django.core.exceptions import MultipleObjectsReturned
from py2neo import neo4j, node, rel
from py2neo.neo4j import GraphDatabaseService as Graph

from apps.assets.models import Category, BaseModel
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
        except (ImportError, AttributeError) as err:
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
            except TypeError as err:
                pass

            # if no custom method is found, dumps it directly (will raise)
            new_things.append(json.dumps(thing))
        return new_things


class GraphWrapper(object):
    """ To create "relationships" between objects, use neo4j nodes to shadow
    django models, like so:

    >>> graph = GraphWrapper()
    >>> products = filter(None, [x.product for x in Tile.objects.filter(
    >>>     id__in=tile_ids)])
    >>> product, other_ones = products[0], products[1:]
    >>> for other_one in other_ones:
    >>>     graph.relate(product, other_one)  # product is now related to these things
    """
    graph = nodes = relationships = None

    # just so it spells "Content Graph";
    # subclasses/you can pick more creative values like "People"
    INDEX_NAME = "Content"

    def __init__(self):
        self.graph = Graph(settings.NEO4J_API_URL)

    def create_node(self, properties=None, key="id", value=None):
        """
        :returns indexed node, with key=value, and other properties.

        If you don't give a value to index by, then the value is properties.id.
        """
        if isinstance(properties, BaseModel):
            # over the special id that is used to denote a model
            value = self.get_model_key(properties)
        elif not value:
            value = getattr(properties, key, "")

        db_node = self.graph.get_or_create_indexed_node(
            self.INDEX_NAME, key, value)

        if isinstance(properties, BaseModel):
            db_node.set_properties(self.model_to_dict(properties))
        else:
            db_node.set_properties({key: value})
        return db_node

    def model_to_dict(self, thing):
        return {
            "id": self.get_model_key(thing),
            "name": repr(thing),
            "class_name": thing.__class__.__name__,
            "model_id": thing.id,
        }

    @property
    def relationship_types(self):
        return self.graph.relationship_types or {}

    def relate(self, thing1, thing2, relation="IS RELATED TO", weight=1):
        """
        :param thing1    either a Node or a BaseModel.
        :param thing2    either a Node or a BaseModel.

        :returns the relationship that relates thing1 to thing2, or... the
        existing one(s) if it/they exist.

        caution: relationships are a one-way street
        """
        if not isinstance(thing1, neo4j.Node):
            thing1 = self.create_node(properties=thing1)
        if not isinstance(thing2, neo4j.Node):
            thing2 = self.create_node(properties=thing2)

        existing_relationships = self.graph.match(start_node=thing1,
            end_node=thing2, rel_type=relation)

        try:
            return next(existing_relationships)
        except StopIteration:  # does not exist
            return self.graph.create(rel(thing1, relation, thing2,
                                         {"weight": weight}))[0]

    @classmethod
    def get_model(cls, db_node):
        """Convert a Node to a BaseModel, assuming the node was previously made
        from a BaseModel.
        """
        prop_bag = db_node.get_properties()
        if not ('class_name' in prop_bag and 'model_id' in prop_bag):
            raise ValueError("{} is not a model node".format(db_node))

        klass = None
        class_name = prop_bag['class_name']
        model_id = prop_bag['model_id']
        try:
            klass = getattr(importlib.import_module('apps.assets.models'),
                class_name)
            return klass.objects.get(id=model_id)
        except MultipleObjectsReturned:
            return klass.objects.filter(id=model_id)[0]
        except ImportError:
            print "failed to create {0}({1})".format(class_name, model_id)
            raise

    def get_model_node(self, model):
        return self.graph.get_indexed_node(self.INDEX_NAME, 'id',
            self.get_model_key(model))

    @classmethod
    def get_weight(cls, relationship):
        try:
            return relationship.get_properties()['weight']
        except KeyError:
            return 0

    @classmethod
    def set_weight(cls, relationship, weight):
        relationship.get_properties({'weight': weight})

    @classmethod
    def get_model_key(cls, model):
        """<Product #123> -> 'Product:123'"""
        return '{0}:{1}'.format(model.__class__.__name__, model.id)

    def unrelate(self, thing1, thing2):
        pass
