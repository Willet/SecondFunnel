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
        self._algorithm = algorithm

    def random(self, num_results=20):
        """"""

    # client side shown
    # product tiles
    # content tiles
    # video tiles
