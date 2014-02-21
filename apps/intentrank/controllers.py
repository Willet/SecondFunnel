import importlib
import json

from django.core import serializers


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

    def __init__(self, feed, algorithm_name='random'):
        """
        :param {Feed} feed   a Feed object with products
        """
        self.feed = feed
        if not feed:
            raise ValueError("Feed must exist, and must contain one item")
        if algorithm_name:
            self.set_algorithm(algorithm_name=algorithm_name)

    def set_algorithm(self, algorithm_name):
        try:
            module = importlib.import_module('apps.intentrank.algorithms')
            print module
            alg = getattr(module, algorithm_name)
        except (ImportError, AttributeError) as err:
            raise AttributeError("IR algorithm {0} does not exist".format(
                algorithm_name))
        print "setting alg to {0}".format(alg)
        self._algorithm = alg

    def get_results(self, format='json', *args, **kwargs):
        """Loads results from the feed, selects some from them
        (given conditions), and transforms these results into the format
        requested.

        :returns {*}
        """
        results = self._algorithm(self.feed, *args, **kwargs)
        return self._transform(results)

    def _transform(self, things, format='json'):
        """Virtual-repr() the thing using whichever serialization method
        makes sense.
        """
        new_things = []
        if format == 'json':
            for thing in things:
                try:
                    new_things.append(json.dumps(thing))
                except TypeError as err:
                    pass

                if hasattr(thing, 'to_json'):
                    new_things.append(thing.to_json())
                else:
                    new_things.append(serializers.serialize('json', thing))
            return new_things
        elif format == 'raw':
            return things
