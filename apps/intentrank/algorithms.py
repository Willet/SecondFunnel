"""Put all IR algorithms here. All algorithms must accept a <Feed>
as the first positional argument, with all other arguments being kwargs.

All algorithms must return <list>.
"""
import math
import random as real_random

from django.conf import settings
import time


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


def ir_popular(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS, request=None, *args, **kwargs):
    prioritized_tiles = prioritized_tile_ids = []
    if request and hasattr(request, 'session'):
        if len(request.session.get('shown', [])) == 0:
            prioritized_tiles = list(
                feed.tiles
                .filter(prioritized=True)
                .order_by('updated_at')
                .select_related()
                .prefetch_related('content', 'products'))
            prioritized_tile_ids = [tile.old_id or tile.id
                                    for tile in prioritized_tiles]

            tiles = list(feed.tiles.exclude(old_id__in=prioritized_tile_ids).select_related().prefetch_related('content', 'products'))

            tiles = sorted(tiles, key=lambda tile: tile.score, reverse=True)

            return (prioritized_tiles + tiles)[:results]

    prioritized_length = len(prioritized_tiles)

    tiles = list(feed.tiles.exclude(old_id__in=prioritized_tile_ids).select_related().prefetch_related('content', 'products'))

    total_score = 0

    for tile in tiles:
        total_score += tile.log_score

    tiles_length = 0
    rand_sum = 0

    if len(tiles) + prioritized_length < results:
        results = len(tiles) + prioritized_length

    while tiles_length + prioritized_length < results:
        rand_num = real_random.uniform(rand_sum, total_score)
        for tile in tiles:
            log_score = tile.log_score
            rand_num -= log_score
            if rand_num <= 0:
                index = tiles.index(tile)
                tiles[tiles_length], tiles[index] = tiles[index], tiles[tiles_length]
                rand_sum += log_score
                tiles_length += 1
                break

    return (prioritized_tiles + tiles)[:results]


def ir_random(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
              product_tiles_only=False, content_tiles_only=False,
              exclude_set=None, request=None, *args, **kwargs):
    """Sample without replacement (all other algos are stubs)

    :param feed: <Feed>
    :param results: int (number of results you want)
    :param product_tiles_only: only select from the Feed's product pool.
    :param content_tiles_only: only select from the Feed's content pool.
    :param exclude_set: <list<int>> do not return tiles with these ids.
    :param request: if supplied, do not return results used in
                    the previous session call, or tile ids specified by the
                    "?shown=" parameter.
    :returns list
    """
    # serve prioritized ones first
    prioritized_tiles = prioritized_tile_ids = []
    if request and hasattr(request, 'session'):
        if len(request.session.get('shown', [])) == 0:
            prioritized_tiles = list(
                feed.tiles
                .filter(prioritized=True)
                .order_by('updated_at')
                .select_related()
                .prefetch_related('content', 'products'))
            prioritized_tile_ids = [tile.old_id or tile.id
                                    for tile in prioritized_tiles]

    # get (10 - number of prioritized) tiles that are not already prioritized
    tiles = list(
        feed.tiles
        .exclude(old_id__in=exclude_set)
        .exclude(old_id__in=prioritized_tile_ids)
        .select_related()
        .prefetch_related('content', 'products')
        # "Note: order_by('?') queries may be expensive and slow..."
        .order_by("?")
        [:results - len(prioritized_tiles)])

    real_random.shuffle(tiles)

    tiles = prioritized_tiles + tiles
    return tiles[:results]


def ir_random_repeat(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                     *args, **kwargs):
    """sample with replacement"""
    raise NotImplementedError()
