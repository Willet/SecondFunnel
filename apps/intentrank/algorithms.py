"""Put all IR algorithms here. All algorithms must accept a <Feed>
as the first positional argument, with all other arguments being kwargs.

All algorithms must return <list>.
"""
import random as real_random

from django.conf import settings


def ir_all(feed, *args, **kwargs):
    """sample whichever ones come last"""
    return list(feed.tiles.all())


def ir_first(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
          *args, **kwargs):
    """sample whichever ones come first"""
    return feed.tiles.order_by('id')[:results]


def ir_last(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
         *args, **kwargs):
    """sample whichever ones come last"""
    return feed.tiles.order_by('id')[:-results]


def ir_random(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
           product_tiles_only=False, content_tiles_only=False,
           exclude_set=None, request=None, *args, **kwargs):
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
    tiles = list(feed.tiles.all())
    real_random.shuffle(tiles)
    return tiles[:results]


def ir_random_repeat(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                  *args, **kwargs):
    """sample with replacement"""
    raise NotImplementedError()
