import timeit
import urllib2

from django.utils.unittest.case import TestCase

from apps.utils import proxy
from apps.utils.mapper import parallel_map, parallelize_lambdas


class ParallelMapTestCase(TestCase):
    """Unit tests the parallel_map function."""

    urls = ['http://www.foxnews.com/',
            'http://www.cnn.com/',
            'http://www.bbc.co.uk/']

    def no_par_fn(self):
        for url in self.__class__.urls:
            try:
                conn = urllib2.urlopen(url, timeout=2)
                conn.readall()
            except:
                pass

    def par_fn(self):
        def fn(url):
            conn = urllib2.urlopen(url, timeout=2)
            conn.readall()

        return parallel_map(fn, self.__class__.urls,
                            raise_on_exceptions=False)

    def test_map_nothing(self):

        new_list = parallel_map(proxy, [])
        self.assertEqual(new_list, [])

        new_list = parallel_map(proxy, [1, 2, 3])
        self.assertEqual(new_list, [1, 2, 3])

    def test_map_transform(self):
        def square(x):
            return x * x

        new_list = parallel_map(square, [1, 2, 3])
        self.assertEqual(new_list, [1, 4, 9])

    def test_map_lambda(self):
        new_list = parallel_map(lambda x: x * x, [1, 2, 3])
        self.assertEqual(new_list, [1, 4, 9])

    def test_map_except(self):
        with self.assertRaises(ZeroDivisionError) as err:
            new_list = parallel_map(lambda x: 1 / x, [0, 1, 2])

        try:
            new_list = parallel_map(lambda x: 1 / x, [0, 1, 2],
                                    raise_on_exceptions=False)
        except ZeroDivisionError:
            self.fail('did not ignore per-item exception')

    def test_map_performance_net_positive(self):
        """check if parallelization actually does something.

        While this may pass in general, it is dependent on cpu speed,
        cpu core count, cpu load, and network load.
        """
        no_par = timeit.Timer(self.no_par_fn).timeit(20)
        par = timeit.Timer(self.par_fn).timeit(20)
        self.assertGreater(no_par, par)


class ParallelizeLambdaTestCase(TestCase):
    """Unit tests the parallel_map function."""
    def test_map_nothing(self):
        """run zero functions, expect zero results"""
        new_list = parallelize_lambdas([])
        self.assertEqual(new_list, [])

    def test_map_per_item(self):
        # run functions that accept zero arguments, expect results
        new_list = parallelize_lambdas([lambda: 1, lambda: 2])
        self.assertEqual(new_list, [1, 2])

        # run functions that accept one argument, expect results
        new_list = parallelize_lambdas([(lambda x: x, 1), (lambda x: x, 2)])
        self.assertEqual(new_list, [1, 2])

        # run function that accepts arbitrary positional arguments, expect results
        new_list = parallelize_lambdas([
            (lambda x, y, z: x + y + z, 1, 2, 3)
        ])
        self.assertEqual(new_list, [6])
