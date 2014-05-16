import importlib
import json
from django.conf import settings

from django.core import serializers
from algorithms import ir_generic
from apps.assets.models import Tile


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

        algorithm = getattr(self, 'ir_' + algorithm_name)
        if algorithm:
            return algorithm

        # verbose fallback
        print "Algorithm 'ir_{0}' not found; using ir_generic instead.".format(
            algorithm_name)
        return self.ir_generic

    def set_algorithm(self, algorithm):
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
        elif serialize_format == 'xml':
            raise NotImplementedError()
        else:
            raise ValueError("Could not understand requested "
                             "serialize_format {0}".format(serialize_format))


class PredictionIOInstance(object):
    def __init__(self, apiurl=settings.PREDICTION_IO_API_URL):
        import predictionio
        # move those if/when used elsewhere
        self.client = predictionio.Client(
            appkey=settings.PREDICTION_IO_API_KEY,
            apiurl=apiurl)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'client'):
            self.client.close()

    def set_user(self, request):
        self.client.create_user(request.session.session_key)
        self.client.identify(request.session.session_key)

    def track_tile_view(self, request, tile):
        self.set_user(request=request)

        if isinstance(tile, Tile):
            tile = tile.id

        tile_key = 'tile-{0}'.format(tile)
        self.client.create_item(tile_key, ('tile',))
        self.client.arecord_action_on_item("view", tile_key)

    def get_recommended_tiles(self, tile_ids=""):
        """
        :param tile_ids: either a list of tile_ids, or a raw CSV of tile-id
                         that prediction.io uses.

        :returns 404 body: {"message":"Cannot find similar items for item."}
        """
        tile_sim = tile_ids
        if isinstance(tile_ids, list):
            tile_sim = ",".join("tile-{0}".format(i) for i in tile_ids)
        return self.client.get_itemsim_topn("ir_similar", tile_sim, 10)
