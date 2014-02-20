class IntentRank(object):
    """Consider this an engine. Initializing one of those will emulate
    behaviour of a Feed object.
    """
    feed = None
    _algorithm = 'random'

    def __init__(self, feed, algorithm=None):
        """
        :param {Feed} feed   a Feed object with products
        """
        self.feed = feed
        if algorithm:
            self.set_algorithm(algorithm)

    def set_algorithm(self, algorithm):
        try:
            alg = __import__('algorithms.{0}'.format(algorithm))
        except ImportError as err:
            raise AttributeError("IR algorithm {0} does not exist".format(
                algorithm))
        self._algorithm = alg

    def get_results(self, format='json', *args, **kwargs):
        return self._transform(self._algorithm(*args, **kwargs))

    def _transform(self, things):
        """Virtual-repr() the thing using whichever serialization method
        makes sense.
        """
        return things

    # client side shown
    # product tiles
    # content tiles
    # video tiles
