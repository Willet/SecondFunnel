import importlib
import json

from django.conf import settings
from django.core import serializers
from py2neo import neo4j, node, rel
from py2neo.neo4j import GraphDatabaseService as Graph

from apps.assets.models import Category
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
    graph = nodes = relationships = None

    INDEX_NAME = "Nodes"  # you can pick more creative values like "People"

    def __init__(self):
        self.graph = Graph(settings.NEO4J_API_URL)
        self.nodes = self.graph.get_or_create_index(  # for lookups
                                                      neo4j.Node, self.INDEX_NAME)
        self.relationships = self.graph.get_or_create_index(  # for lookups
                                                              neo4j.Relationship, self.INDEX_NAME)

        a, b, ab = self.graph.create(node(name="Alice"), node(name="Bob"), rel(0, "KNOWS", 1))
        c = 1

    def create_nodes(self, *nodes_and_rels):
        return self.graph.create(*nodes_and_rels)

    def model_to_dict(self, thing):
        return {
            "id": repr(thing),
            "class_name": thing.__class__.__name__,
            "model_id": thing.id
        }

    def get_nodes(self, node_id):
        return self.nodes.get('id', node_id)

    def get_or_create_node(self, node_id):
        return self.graph.get_or_create_indexed_node("nodes", "id", node_id)

    def relate(self, thing1, thing2, relation="IS RELATED TO", weight=1):
        # caution: is directional
        return self.graph.create(
            node(self.model_to_dict(thing1)),
            node(self.model_to_dict(thing2)),
            rel(0, relation, 1, {"weight": weight}))  # relation can be 'PLAYS', 'LIKES', ...

    def unrelate(self, thing1, thing2):
        pass


class BulbWrapper(object):
    # GREMLIN IS REQUIRED
    def __init__(self):
        from bulbs.neo4jserver import Graph, Config
        config = Config(settings.NEO4J_API_URL)
        self.graph = Graph(config)

        self.wat()

    def get_edges(self):
        return self.graph.E

    def wat(self):
        self.graph.vertices.create(name="Bob")


class Neo4JDBWrapper(object):
    def __init__(self):
        import neo4j
        connection = neo4j.connect(settings.NEO4J_API_URL)
        cursor = connection.cursor()
        for node in cursor.execute("MATCH (n) RETURN n"):
            print node
