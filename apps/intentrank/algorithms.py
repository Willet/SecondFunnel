"""Put all IR algorithms here. All algorithms must accept a <Feed>
as the first positional argument, with all other arguments being kwargs.

All algorithms must return <list>.
"""
from functools import partial
import random as real_random

from django.conf import settings


def ids_of(tiles):  # shorthand (got too annoying)
    return [getattr(tile, 'old_id', getattr(tile, 'id')) for tile in tiles]


def ir_all(feed, *args, **kwargs):
    """sample whichever ones come last"""
    return list(feed.tiles.all())


def ir_first(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
             allowed_set=None, *args, **kwargs):
    """sample whichever ones come first"""
    # serve prioritized ones first
    if results < 1:
        return []

    tile_filter = {'prioritized': True}

    if allowed_set:
        tile_filter.update({'old_id__in': allowed_set})

    prioritized_tiles = list(
        feed.tiles
        .filter(**tile_filter)
        .order_by('updated_at')
        .select_related()
        .prefetch_related('content', 'products'))

    tile_filter.pop('prioritized')

    return prioritized_tiles + list(feed.tiles.filter(**tile_filter).order_by('id')[:results])


def ir_last(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
            allowed_set=None, *args, **kwargs):
    """sample whichever ones come last"""
    if results < 1:
        return []

    tile_filter = {}

    if allowed_set:
        tile_filter.update({'old_id__in': allowed_set})

    return list(feed.tiles.filter(**tile_filter).order_by('id')[:-results])


def ir_prioritized(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                   prioritized_set='', exclude_set=None, allowed_set=None):
    """Return prioritized tiles in the feed, ordered by priority,
    except the ones in exclude_set, which is a list of old id integers.
    """
    if results < 1:
        return []

    tile_filter = {'prioritized': prioritized_set}

    if allowed_set:
        tile_filter.update({'old_id__in': allowed_set})

    tiles = feed.tiles.filter(**tile_filter)
    if exclude_set:
        tiles = tiles.exclude(old_id__in=exclude_set)

    tiles = (tiles.order_by('created_at')
                  .select_related()
                  .prefetch_related('content', 'products')
                  .order_by('-priority', '?'))

    tiles = list(tiles[:results])

    print "{0} tile(s) were manually prioritized by {1}".format(
        len(tiles), prioritized_set or 'nothing')

    return tiles


ir_priority_request = partial(ir_prioritized, prioritized_set='request')
ir_priority_pageview = partial(ir_prioritized, prioritized_set='pageview')
ir_priority_session = partial(ir_prioritized, prioritized_set='session')
ir_priority_cookie = partial(ir_prioritized, prioritized_set='cookie')
ir_priority_custom = partial(ir_prioritized, prioritized_set='custom')


def ir_priority_sorted(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                       prioritized_state=True, exclude_set=None, allowed_set=None):
    """Return prioritized tiles in the feed, ordered by their priority values,
    except the ones in exclude_set, which is a list of old id integers.
    """

    if results < 1:
        return []

    tile_filter = {'prioritized': prioritized_state}

    if allowed_set:
        tile_filter.update({'old_id__in': allowed_set})

    tiles = feed.tiles.filter(**tile_filter)

    if exclude_set:
        tiles = tiles.exclude(old_id__in=exclude_set)

    tiles = (tiles.order_by('-priority')
                  .select_related()
                  .prefetch_related('content', 'products'))

    tiles = list(tiles[:results])

    print "{0} tile(s) were manually prioritized".format(len(tiles))

    return tiles


def ir_random(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
              exclude_set=None, allowed_set=None):
    """get (a numbr of) random tiles, except the ones in exclude_set,
    which is a list of old id integers."""
    if results < 1:
        return []

    tile_filter = {}

    if allowed_set:
        tile_filter.update({'old_id__in': allowed_set})

    tiles = feed.tiles.filter(**tile_filter)
    if exclude_set:
        tiles = tiles.exclude(old_id__in=exclude_set)

    tiles = (tiles.select_related()
                  .prefetch_related('content', 'products')
                  # "Note: order_by('?') queries may be expensive and slow..."
                  .order_by("?"))

    tiles = list(tiles[:results])

    print "{0} tile(s) were randomly added".format(len(tiles))

    real_random.shuffle(tiles)
    return tiles


def ir_created_last(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                    exclude_set=None, allowed_set=None):
    """Return most recently-created tiles in the feed, except the ones in
    exclude_set, which is a list of old id integers.
    """
    if results < 1:
        return []

    tile_filter = {}

    if allowed_set:
        tile_filter.update({'old_id__in': allowed_set})

    tiles = feed.tiles.filter(**tile_filter)

    if exclude_set:
        tiles = tiles.exclude(old_id__in=exclude_set)

    tiles = (tiles.select_related()
                  .prefetch_related('content', 'products')
                  .order_by("-created_at"))

    tiles = list(tiles[:results])

    print "{0} tile(s) were automatically prioritized by -created".format(len(tiles))
    return tiles


def ir_popular(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
               product_tiles_only=False, content_tiles_only=False,
               request=None, exclude_set=None, allowed_set=None,
               *args, **kwargs):
    """Sample without replacement
    returns tiles with a higher chance for a tile to be returned if it is a popular tile

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
    if results < 1:
        return []

    tile_filter = {}

    if allowed_set:
        tile_filter.update({'old_id__in': allowed_set})

    tiles = feed.tiles.filter(**tile_filter)

    if exclude_set:
        tiles = tiles.exclude(old_id__in=exclude_set)

    tiles = (tiles.select_related()
                  .prefetch_related('content', 'products'))

    tiles = sorted(tiles, key=lambda tile: tile.click_score(), reverse=True)

    return tiles[:results]


def ir_generic(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
               product_tiles_only=False, content_tiles_only=False,
               exclude_set=None, allowed_set=None, request=None,
               *args, **kwargs):
    """Return tiles in the following order:

    - prioritized ones
      - by custom (not implemented)
      - by request
      - by pageview
      - by session
      - by cookie (not implemented)
    - new ones
    - other ones

    with no repeat.

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
    num_new_tiles_to_autoprioritize = 8  # "show new tiles first"

    # first, always show the ones that are 'request' i.e. every request
    prioritized_tiles += ir_priority_request(feed=feed, results=1000,
                                             exclude_set=exclude_set)

    # second, show the ones for the first request
    if request and request.GET.get('reqNum', 0) in [0, '0']:
        prioritized_tiles += ir_priority_pageview(feed=feed, results=1000,
                                                  exclude_set=exclude_set)
        prioritized_tile_ids = ids_of(prioritized_tiles)

    if len(prioritized_tiles) >= results:
        return prioritized_tiles[:results]

    # third, show the ones that have never been shown in this session
    if request and hasattr(request, 'session'):
        if len(request.session.get('shown', [])) == 0:  # first page view
            prioritized_tiles += ir_priority_session(feed=feed, results=8,
                exclude_set=prioritized_tile_ids)
            exclude_set += ids_of(prioritized_tiles)

            # fill the first two rows with (8) tiles that are known to be new
            new_tiles = ir_created_last(feed=feed, exclude_set=exclude_set,
                                        allowed_set=allowed_set,
                                        results=num_new_tiles_to_autoprioritize)
            real_random.shuffle(new_tiles)

            prioritized_tiles += new_tiles

    if len(prioritized_tiles) >= results:
        return prioritized_tiles[:results]

    prioritized_tile_ids = ids_of(prioritized_tiles)

    # get (10 - number of prioritized) tiles that are not already prioritized
    random_tiles = ir_random(feed=feed,
                             results=(results - len(prioritized_tiles)),
                             exclude_set=prioritized_tile_ids,
                             allowed_set=allowed_set)

    tiles = prioritized_tiles + random_tiles
    return tiles[:results]


def ir_ordered(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
               product_tiles_only=False, content_tiles_only=False,
               exclude_set=None, allowed_set=None, request=None,
               *args, **kwargs):
    """Return tiles in the following order:

    - prioritized ones (ordered by priority)
    - other ones (also ordered by priority)

    with no repeat.

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
    if not (request and hasattr(request, 'session')):
        raise ValueError("Sessions must be enabled for ir_ordered")

    # first, always show the ones that are 'request' i.e. every request
    prioritized_tiles += ir_priority_request(feed=feed, results=1000,
                                             exclude_set=exclude_set,
                                             allowed_set=allowed_set)
    if len(prioritized_tiles) >= results:
        return prioritized_tiles[:results]

    # second, show the ones for the first request
    exclude_set += ids_of(prioritized_tiles)
    if request and request.GET.get('reqNum', 0) in [0, '0']:
        prioritized_tiles += ir_priority_pageview(feed=feed, results=1000,
                                                  exclude_set=exclude_set,
                                                  allowed_set=allowed_set)
    else:  # else... NEVER show these per-request tiles again
        x_prioritized_tiles = ir_priority_pageview(feed=feed, results=1000,
                                                   exclude_set=exclude_set,
                                                   allowed_set=allowed_set)
        exclude_set += ids_of(x_prioritized_tiles)
    if len(prioritized_tiles) >= results:
        return prioritized_tiles[:results]

    # fill the first two rows with (8) tiles that are known to be new
    exclude_set += ids_of(prioritized_tiles)
    if len(request.session.get('shown', [])) == 0:  # first page view
        prioritized_tiles += ir_created_last(feed=feed, results=8,
                                             exclude_set=exclude_set,
                                             allowed_set=allowed_set)
    if len(prioritized_tiles) >= results:
        return prioritized_tiles[:results]

    # get (10 - number of prioritized) tiles that are not already prioritized
    exclude_set += ids_of(prioritized_tiles)
    random_tiles = ir_prioritized(feed=feed, prioritized_set='',
        results=(results - len(prioritized_tiles)),
        exclude_set=exclude_set,
        allowed_set=allowed_set)

    real_random.shuffle(random_tiles)

    tiles = prioritized_tiles + random_tiles
    return tiles[:results]
