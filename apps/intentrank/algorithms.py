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
    # serve prioritized ones first
    prioritized_tiles = list(
        feed.tiles
        .filter(prioritized=True)
        .order_by('updated_at')
        .select_related()
        .prefetch_related('content', 'products'))

    return prioritized_tiles + list(feed.tiles.order_by('id')[:results])


def ir_last(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
            *args, **kwargs):
    """sample whichever ones come last"""
    return list(feed.tiles.order_by('id')[:-results])


def ir_prioritized(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                   exclude_set=None):
    """Return prioritized tiles in the feed, ordered randomly,
    except the ones in exclude_set, which is a list of old id integers.
    """
    tiles = list(
        feed.tiles
            .filter(prioritized=True)
            .exclude(old_id__in=exclude_set)
            .order_by('created_at')
            .select_related()
            .prefetch_related('content', 'products')
            .order_by('?')[:results])

    print "{0} tile(s) were manually prioritized".format(len(tiles))

    return tiles


def ir_priority_sorted(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                       prioritized_state=True, exclude_set=None):
    """Return prioritized tiles in the feed, ordered by their priority values,
    except the ones in exclude_set, which is a list of old id integers.
    """
    tiles = list(
        feed.tiles
            .filter(prioritized=prioritized_state)
            .exclude(old_id__in=exclude_set)
            .order_by('-priority')
            .select_related()
            .prefetch_related('content', 'products')
            [:results])

    print "{0} tile(s) were manually prioritized".format(len(tiles))

    return tiles


def ir_random(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
              exclude_set=None):
    """get (a numbr of) random tiles, except the ones in exclude_set,
    which is a list of old id integers."""
    tiles = list(
        feed.tiles
            .exclude(old_id__in=exclude_set)
            .select_related()
            .prefetch_related('content', 'products')
            # "Note: order_by('?') queries may be expensive and slow..."
            .order_by("?")[:results])

    print "{0} tile(s) were randomly added".format(len(tiles))

    real_random.shuffle(tiles)
    return tiles


def ir_created_last(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                    exclude_set=None):
    """Return most recently-created tiles in the feed, except the ones in
    exclude_set, which is a list of old id integers.
    """
    tiles = list(
        feed.tiles
            .exclude(old_id__in=exclude_set)
            .select_related()
            .prefetch_related('content', 'products')
            .order_by("-created_at")[:results])

    print "{0} tile(s) were automatically prioritized".format(len(tiles))
    return tiles


def ir_popular(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
               product_tiles_only=False, content_tiles_only=False,
               request=None, exclude_set=None, *args, **kwargs):
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

    tiles = list(feed.tiles.exclude(old_id__in=exclude_set)
        .select_related().prefetch_related('content', 'products'))

    tiles = sorted(tiles, key=lambda tile: tile.click_score(), reverse=True)

    return tiles[:results]


def ir_generic(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
               product_tiles_only=False, content_tiles_only=False,
               exclude_set=None, request=None, *args, **kwargs):
    """Return tiles in the following order:

    - prioritized ones
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
    if request and hasattr(request, 'session'):
        if len(request.session.get('shown', [])) == 0:  # first page view
            prioritized_tiles = ir_prioritized(feed=feed, results=8,
                                               exclude_set=exclude_set)

            # fill the first two rows with (8) tiles that are known to be new
            exclude_set += [tile.old_id for tile in prioritized_tiles]
            new_tiles = ir_created_last(
                feed=feed,
                results=(num_new_tiles_to_autoprioritize - len(prioritized_tiles)),
                exclude_set=exclude_set)
            real_random.shuffle(new_tiles)

            prioritized_tiles += new_tiles
            prioritized_tile_ids = [tile.old_id or tile.id
                                    for tile in prioritized_tiles]

    # get (10 - number of prioritized) tiles that are not already prioritized
    random_tiles = ir_random(feed=feed,
                             results=(results - len(prioritized_tiles)),
                             exclude_set=prioritized_tile_ids)

    tiles = prioritized_tiles + random_tiles
    return tiles[:results]


def ir_ordered(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
               product_tiles_only=False, content_tiles_only=False,
               exclude_set=None, request=None, *args, **kwargs):
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

    if len(request.session.get('shown', [])) == 0:  # first page view
        prioritized_tiles = ir_priority_sorted(feed=feed, results=8,
                                               exclude_set=exclude_set)

        # fill the first two rows with (8) tiles that are known to be new
        exclude_set += [tile.old_id for tile in prioritized_tiles]
        prioritized_tile_ids = [tile.old_id or tile.id
                                for tile in prioritized_tiles]

    # get (10 - number of prioritized) tiles that are not already prioritized
    random_tiles = ir_priority_sorted(feed=feed, prioritized_state=False,
        results=(results - len(prioritized_tiles)),
        exclude_set=prioritized_tile_ids)

    tiles = prioritized_tiles + random_tiles
    return tiles[:results]
