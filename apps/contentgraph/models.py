import importlib
import json

from django.core.exceptions import MultipleObjectsReturned
from django.conf import settings
import hammock
from py2neo import neo4j, rel
from py2neo.neo4j import GraphDatabaseService as Graph, ReadBatch, WriteBatch

from apps.assets.models import BaseModel

ContentGraphClient = hammock.Hammock(settings.CONTENTGRAPH_BASE_URL,
                                     headers={'ApiKey': 'secretword'})


def get_contentgraph_data(endpoint_path, headers=None, method="GET",
                          params=None, body=""):
    """Wraps all contentgraph requests with the required api key.

    return will be a json dict, or a string if deserialization fails.
    """
    if not params:
        params = {}

    if not headers:
        headers = {}

    headers.update({'ApiKey': 'secretword'})

    # same as the ContentGraphClient above, with variable headers
    contentgraph_client = hammock.Hammock(settings.CONTENTGRAPH_BASE_URL,
        headers=headers)

    while True:
        # getattr used to retrieve GET/POST magic methods
        method_handler = getattr(contentgraph_client(endpoint_path), method)
        response = method_handler(params=params, data=body)

        # raise errors defined by the Requests library (400s, 500s, 600s)
        response.raise_for_status()

        content = response.json()

        # - 'meta' is an object if the call is paginated
        # - 'meta' cannot be an object if the object itself has an
        #       attribute named 'meta' (dynamodb limitation)
        if 'meta' in content:
            if isinstance(content['meta'], dict):  # is CG meta
                if 'cursors' in content['meta'] and 'next' in content['meta']['cursors']:
                    if not isinstance(content['results'], list):
                        # validate and raise, because we love that
                        raise TypeError(
                            'Paginated call expects [results] to be list; '
                            'got [{0}] instead'.format(
                                type(content['results'])))

                    for result in content['results']:
                        yield result
                        params['offset'] = content['meta']['cursors']['next']

                else:  # end of page
                    for result in content['results']:
                        yield result
                    break  # trigger StopIteration
            else:  # is user-defined meta
                yield content
                break  # trigger StopIteration
        else:  # not paginated call
            yield content
            break  # trigger StopIteration


def call_contentgraph(*args, **kwargs):
    """function-alias for the get_contentgraph_data generator.

    Returns one result (the first one by the generator).
    """
    return next(get_contentgraph_data(*args, **kwargs))


class ContentGraphObject(object):
    """object representation of any CG endpoint.

    This object is not bound to a database, and cannot be saved unless data
    is transferred to another model.
    """
    endpoint_path = '/'
    cached_data = {}

    def __init__(self, endpoint_path, auto_create=False):
        """supply a path to connect to, e.g. /store/126.

        @param {boolean} auto_create        create this object if it is missing
        """
        self.endpoint_path = endpoint_path
        if auto_create:
            call_contentgraph(endpoint_path=endpoint_path, method="PUT",
                              body=json.dumps({}))

        self.cached_data = call_contentgraph(endpoint_path=self.endpoint_path)

    def data(self):
        if self.cached_data:
            return self.cached_data

        result = call_contentgraph(endpoint_path=self.endpoint_path)
        self.cached_data = result

        return self.cached_data

    def get(self, item, default_value=None):
        # dict method
        return self.data().get(item, default_value)

    def set(self, key, value):
        if key == 'endpoint_path':
            return

        # apparently, objects with __setattr__ just skip over this
        setattr(self, key, value)

        # send it back to the server
        return call_contentgraph(endpoint_path=self.endpoint_path,
            method="PATCH", body=json.dumps({key: value}))

    def json(self, serialized=True):
        if serialized:
            return json.dumps(self.cached_data)
        else:
            return self.cached_data


class TileConfigObject(object):
    """Suppose the tile config generator does something. This object
    is a pseudo-controller that tells the real generator to do stuff.
    """

    clients = []

    def __init__(self, store_id=None, page_id=None):
        """Supply either store_id or page_id, not both.

        Supplying page_id is faster.
        If store_id is given, performs actions on all pages for the store.
        """
        if page_id:
            # this is only one page
            self.clients = [ContentGraphClient.page(page_id)('tile-config')]
        elif store_id:
            # this is a store worth of pages
            page_ids = [x['id'] for x in get_contentgraph_data(
                '/store/{0}/page?select=id'.format(store_id))]
            self.clients = [ContentGraphClient.page(page_id)('tile-config')
                            for page_id in page_ids]
        else:  # given none of those
            raise ValueError("Need store_id or page_id")

    def get_all(self):
        """Get all configs for all pages in this client.

        @returns list{list}
        @raises IndexError
        """
        result = []
        for client in self.clients:
            result.append(client.GET().json()['results'])
        return result

    def get(self, config_id):
        """Get one config.

        @returns list{dict}
        @raises IndexError
        """
        result = []
        for client in self.clients:
            result.append(client(config_id).GET().json())
        return result

    def update_config(self, config_id, new_props):
        """merges a dict given with the existing tile config."""
        result = []
        for client in self.clients:
            result.append(client(config_id).PATCH(data=json.dumps(new_props)).json())
        return result

    def mark_tile_for_regeneration(self, content_id=None, product_id=None):
        """Mark all tile configs for this product/content for regeneration.

        If content_id is given, processes that content's tile config.
        If product_id is given, processes that product's tile config.
        """
        if content_id:
            query_key = 'content-ids'
        else:
            query_key = 'product-ids'

        # list
        for client in self.clients:
            tile_configs = client.GET(
                params={query_key: content_id or product_id}).json()['results']

            # dicts
            for tile_config in tile_configs:
                client(tile_config['id']).PATCH(
                    # TODO: might need concurrency checking
                    params={'version': tile_config['last-modified']},
                    data={'stale': 'true'})  # yes, a string 'true'
                # TODO: version/last-modified


class GraphWrapper(object):
    """ To create "relationships" between objects, use neo4j nodes to shadow
    django models, like so:

    >>> graph = GraphWrapper()
    >>> products = Product.objects.all()
    >>> product, product2 = products[0], products[1]
    >>> graph.relate(product, product2)  # product is now related to product2
    >>> graph.unrelate(product, product2)  # product is now unrelated to product2
    """
    graph = nodes = relationships = _batch = None

    # just so it spells "Content Graph";
    # subclasses/you can pick more creative values like "People"
    INDEX_NAME = "Content"

    # alternatives: "view", "click"
    RELATION_NAME = "IS RELATED TO"

    def __init__(self, graph=None):
        self.graph = graph
        if not graph:
            self.graph = Graph(settings.NEO4J_API_URL)

    def __enter__(self, mode="r"):
        """In a with statement, the object will be used as a collector.

        If you need to both read and write, avoid using the with statement.
        """
        if mode == "r":
            self._batch = ReadBatch(self.graph)
            return self._batch
        elif mode == "w":
            self._batch = WriteBatch(self.graph)
            return self._batch
        raise ValueError("{} is not a Batch mode".format(mode))

    def __exit__(self, exc_type, exc_val, exc_tb):
        # (run) batch!
        if self._batch:
            self._batch.submit()

    def create_node(self, properties=None, key="id", value=None):
        """
        :returns indexed node, with key=value, and other properties.

        If you don't give a value to index by, then the value is properties.id.
        """
        if isinstance(properties, BaseModel):
            # over the special id that is used to denote a model
            value = self._get_model_key(properties)
        elif not value:
            value = getattr(properties, key, "")

        db_node = self.graph.get_or_create_indexed_node(
            self.INDEX_NAME, key, value)

        if isinstance(properties, BaseModel):
            db_node.set_properties(self._model_to_dict(properties))
        else:
            db_node.set_properties({key: value})
        return db_node

    def delete_node(self, node):
        """Apparently just a proxy"""
        return self.graph.delete(node)
    delete_relationship = delete_node

    def _model_to_dict(self, thing):
        return {
            "id": self._get_model_key(thing),
            "name": repr(thing),
            "class_name": thing.__class__.__name__,
            "model_id": thing.id,
        }

    @property
    def relationship_types(self):
        return self.graph.relationship_types or {}

    def relate(self, node1, node2, relation=RELATION_NAME, weight=1):
        """
        :param node1    either a Node or a BaseModel.
        :param node2    either a Node or a BaseModel.

        :returns the relationship that relates node1 to node2, or... the
        existing relation will have its weight incremented by {weight}.

        caution: relationships are a one-way street
        """
        if not isinstance(node1, neo4j.Node):
            node1 = self.create_node(properties=node1)
        if not isinstance(node2, neo4j.Node):
            node2 = self.create_node(properties=node2)

        # find all nodes like the one you're currently making
        existing_relationships = list(self.graph.match(start_node=node1,
            end_node=node2, rel_type=relation))

        if len(existing_relationships):
            existing_relationship = existing_relationships[0]
            self.set_weight(
                existing_relationship,
                weight=self.get_weight(existing_relationship) + weight)

            return existing_relationships[0]
        else:  # does not exist
            return self.graph.create(rel(node1, relation, node2,
                                         {"weight": weight}))[0]

    def _relate_or_create(self, node1, node2, relation=RELATION_NAME, weight=1):
        """If a
        :param node1    either a Node or a BaseModel.
        :param node2    either a Node or a BaseModel.

        :returns the relationship that relates node1 to node2, or... the
        existing one(s) if it/they exist.
        """
        if not isinstance(node1, neo4j.Node):
            node1 = self.create_node(properties=node1)
        if not isinstance(node2, neo4j.Node):
            node2 = self.create_node(properties=node2)

        # find all nodes like the one you're currently making
        existing_relationships = list(self.graph.match(start_node=node1,
            end_node=node2, rel_type=relation))

        if len(existing_relationships):
            existing_relationship = existing_relationships[0]
            return existing_relationship
        else:  # does not exist
            return self.graph.create(rel(node1, relation, node2,
                                         {"weight": weight}))[0]

    def unrelate(self, node1, node2, relation=RELATION_NAME):
        """
        :param node1    either a Node or a BaseModel.
        :param node2    either a Node or a BaseModel.

        Deletes the relationship(s) that point(s) node1 to node2.
        """
        if isinstance(node1, BaseModel):
            node1 = self._get_model_node(node1)
        if isinstance(node2, BaseModel):
            node2 = self._get_model_node(node2)

        if not (node1 and node2):
            raise ValueError("One of these nodes are missing: {}, {}".format(
                node1, node2))

        existing_relationships = self.graph.match(start_node=node1,
                                                  end_node=node2,
                                                  rel_type=relation)

        return self.graph.delete(*list(existing_relationships))

    def get_related_models(self, model, rel_type=None, bidirectional=False):
        """Given a model, get its related models."""
        db_node = self._get_model_node(model=model)
        if not db_node:
            raise ValueError("Node for {} not found".format(model))

        return [self._get_model(db_node=n) for n in
                self._get_related_nodes(db_node=db_node, rel_type=rel_type,
                                        bidirectional=bidirectional)]

    @classmethod
    def _get_model(cls, db_node):
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

    def _get_model_node(self, model):
        """Given a model, get its node.

        Not guaranteed to return anything.
        """
        return self.graph.get_indexed_node(self.INDEX_NAME, 'id',
                                           self._get_model_key(model))

    def _get_relationships(self, db_node, rel_type=None, bidirectional=False):
        """Given db_node, get its relationships...
        - bidirectional True:
            ... with that node in either end.
        - bidirectional False:
            ... with that node as start_node.
        """
        kwargs = {
            "start_node": db_node,
            "bidirectional": bidirectional,
        }
        if rel_type:
            kwargs["rel_type"] = rel_type

        relationships = list(self.graph.match(**kwargs))
        if relationships:
            return relationships
        return []

    def _get_relationships_by_type(self, rel_type=RELATION_NAME):
        """Fast method of retrieving all model relationships of a certain type.

        use of this method is discouraged, because graph internals are exposed.

        :returns set(start_props, end_props, start node, end node)
                 see _get_model_key for id format.
        """
        pairs = []
        for x in self.graph.match(rel_type=rel_type):
            start = x.start_node.get_properties()
            end = x.end_node.get_properties()
            if 'id' in start and 'id' in end:
                pairs.append((start, end, x.start_node, x.end_node))

        return pairs

    def _get_related_nodes(self, db_node, rel_type=None, bidirectional=False):
        """Given db_node, get other nodes...
        - bidirectional True:
            ... connected to it.
        - bidirectional False:
            ... that it connects to.

        Results are ordered by edge weight. no-weight relationships
        have 0 weight.
        """
        relationships = self._get_relationships(db_node=db_node,
                                                rel_type=rel_type,
                                                bidirectional=bidirectional)

        relationships = sorted(relationships, key=self.get_weight,
                               reverse=True)

        nodes = []
        for relation in relationships:
            if relation.start_node == db_node:
                nodes.append(relation.end_node)
            else:
                nodes.append(relation.start_node)
        return nodes

    @staticmethod
    def get_weight(relationship):
        try:
            return relationship.get_properties()['weight']
        except KeyError:
            return 0

    @staticmethod
    def set_weight(relationship, weight):
        return relationship.set_properties({'weight': weight})

    @staticmethod
    def _get_model_key(model):
        """<Product #123> -> 'Product:123'"""
        if not isinstance(model, BaseModel):
            raise ValueError("{} is not a BaseModel".format(model))

        return '{0}:{1}'.format(model.__class__.__name__, model.id)
