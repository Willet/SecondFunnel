import importlib
import json

from django.core import serializers
from algorithms import ir_generic

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
