"""Put all IR algorithms here. All algorithms must accept a <Feed>
as the first positional argument, with all other arguments being kwargs.

All algorithms must return <list>.
"""
import random as real_random

from django.conf import settings


def first(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS):
    """sample whichever ones come first"""
    return feed[:results]


def last(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS):
    """sample whichever ones come last"""
    return feed[:-results]


def random(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
           product_tiles_only=False, content_tiles_only=False,
           exclude_set=None, request=None):
    """Sample without replacement (all other algos are stubs)

    :param feed: <Feed>
    :param results: int (number of results you want)
    :param product_tiles_only: only select from the Feed's product pool.
    :param content_tiles_only: only select from the Feed's content pool.
    :param exclude_set: <list<Tile>> do not return these results.
    :param request: if supplied, do not return results used in
                    the previous session call, or tile ids specified by the
                    "?shown=" parameter.
    :returns list
    """
    print results
    tiles = list(feed.tiles.all())
    real_random.shuffle(tiles)
    return tiles[:results]


def random_repeat(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS):
    """sample with replacement"""
    raise NotImplementedError()
