"""Put all IR algorithms here. All algorithms must accept a <tiles>
as the first positional argument, with all other arguments being kwargs.

All algorithms must return <list>.
"""
from functools import partial, wraps
import random as real_random

from django.conf import settings
from apps.assets.models import Tile
from apps.intentrank.filters import order_by
from apps.utils.functional import result
from apps.intentrank import filters


def ids_of(tiles):  # shorthand (got too annoying)
    return [getattr(tile, 'old_id', getattr(tile, 'id')) for tile in tiles]


def qs_for(tiles):
    """Convert a list of tiles to a queryset containing those tiles.

    Executes at least one query.

    :returns {QuerySet}
    """
    try:
        ids = [x.id for x in tiles]
    except AttributeError:
        ids = tiles

    return (Tile.objects.filter(id__in=ids)
                .prefetch_related(*Tile.ASSOCS)
                .select_related(*Tile.ASSOCS))


def ir_base(tiles=None, feed=None, **kwargs):
    """Common algo for removes tiles that no IR algorithm will ever serve.

    Required parameters: either tiles (list / QuerSet) or feed (<Feed>)

    returns {QuerySet} of {Tile} instances (which is *not* a list)
    """
    if feed:
        tiles = feed.get_tiles()

    if tiles is None:  # permit []
        raise ValueError("Either tiles or feed must be supplied to ir_base")

    # "filter out all content tiles for which none of the content's
    # tagged products are in stock"
    tids = [tile.id for tile in filter(filters.in_stock, tiles)]

    # DO NOT call *_related functions after ir_base!
    return qs_for(tids)


def ir_all(tiles, *args, **kwargs):
    return tiles


def ir_first(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
             allowed_set=None, *args, **kwargs):
    """sample whichever ones come first"""
    # serve prioritized ones first
    if results < 1:
        return []

    tiles = filter(filters.prioritized('any'), tiles)
    prioritized_tiles = order_by(tiles, 'updated_at')

    return (prioritized_tiles + order_by(tiles, 'id'))[:results]


def ir_last(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
            allowed_set=None, *args, **kwargs):
    """sample whichever ones come last"""
    if results < 1:
        return []

    tile_filter = {}

    if allowed_set:
        tile_filter.update({'id__in': allowed_set})

    tiles = tiles.filter(**tile_filter).order_by('id')
    return list(tiles.reverse()[:results])


def ir_prioritized(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                   prioritized_set='', exclude_set=None, allowed_set=None,
                   **kwargs):
    """Return prioritized tiles in the feed, ordered by priority,
    except the ones in exclude_set, which is a list of old id integers.
    """
    if results < 1:
        return []

    if allowed_set:
        tiles = filter(filters.id_in(allowed_set), tiles)
    if exclude_set:
        tiles = filter(filters.id_not_in(exclude_set), tiles)

    tiles = filter(filters.prioritized(prioritized_set), tiles)

    tiles = order_by(tiles, '-priority')
    real_random.shuffle(tiles)
    tiles = tiles[:results]

    print "{0} tile(s) were manually prioritized by {1}".format(
        len(tiles), prioritized_set or 'nothing')

    return tiles


ir_priority_request = partial(ir_prioritized, prioritized_set='request')
ir_priority_pageview = partial(ir_prioritized, prioritized_set='pageview')
ir_priority_session = partial(ir_prioritized, prioritized_set='session')
ir_priority_cookie = partial(ir_prioritized, prioritized_set='cookie')
ir_priority_custom = partial(ir_prioritized, prioritized_set='custom')


def ir_priority_sorted(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                       prioritized_state='any', exclude_set=None,
                       allowed_set=None, **kwargs):
    """Return prioritized tiles in the feed, ordered by their priority values,
    except the ones in exclude_set, which is a list of id integers.
    """

    if results < 1:
        return []

    tiles = filter(filters.id_in(allowed_set), tiles)
    tiles = filter(filters.id_not_in(exclude_set), tiles)
    tiles = filter(filters.prioritized(prioritized_state), tiles)

    tiles = order_by(tiles, '-priority')[:results]

    print "{0} tile(s) were manually prioritized".format(len(tiles))
    return tiles


def ir_random(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
              exclude_set=None, allowed_set=None, **kwargs):
    """get (a numbr of) random tiles, except the ones in exclude_set,
    which is a list of old id integers."""
    if results < 1:
        return []

    tiles = filter(filters.id_in(allowed_set), tiles)
    tiles = filter(filters.id_not_in(exclude_set), tiles)

    real_random.shuffle(tiles)
    tiles = tiles[:results]

    print "{0} tile(s) were randomly added".format(len(tiles))

    return tiles


def ir_created_last(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                    exclude_set=None, allowed_set=None, *args, **kwargs):
    """Return most recently-created tiles in the feed, except the ones in
    exclude_set, which is a list of old id integers.
    """
    if results < 1:
        return []

    tiles = filter(filters.id_in(allowed_set), tiles)
    tiles = filter(filters.id_not_in(exclude_set), tiles)

    tiles = order_by(tiles, "-created_at")[:results]

    print "{0} tile(s) were automatically prioritized by -created".format(len(tiles))
    return tiles


def ir_popular(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
               product_tiles_only=False, content_tiles_only=False,
               request=None, exclude_set=None, allowed_set=None,
               *args, **kwargs):
    """Sample without replacement
    returns tiles with a higher chance for a tile to be returned if it is a popular tile

    :param tiles: [Tile]
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

    tiles = filter(filters.id_in(allowed_set), tiles)
    tiles = filter(filters.id_not_in(exclude_set), tiles)

    tiles = sorted(tiles, key=lambda tile: tile.click_score(), reverse=True)

    return tiles[:results]


def ir_generic(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
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

    :param tiles: [<Tile>]
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
    prioritized_tiles += ir_priority_request(tiles=tiles, results=10,
                                             exclude_set=exclude_set,
                                             allowed_set=allowed_set)

    # second, show the ones for the first request
    if request and request.GET.get('reqNum', 0) in [0, '0']:
        prioritized_tiles += ir_priority_pageview(tiles=tiles, results=10,
                                                  exclude_set=exclude_set,
                                                  allowed_set=allowed_set)
        prioritized_tile_ids = ids_of(prioritized_tiles)

    if len(prioritized_tiles) >= results:
        return prioritized_tiles[:results]

    # third, show the ones that have never been shown in this session
    if request and hasattr(request, 'session'):
        if len(request.session.get('shown', [])) == 0:  # first page view
            prioritized_tiles += ir_priority_session(tiles=tiles, results=8,
                exclude_set=prioritized_tile_ids,
                allowed_set=allowed_set)
            exclude_set += ids_of(prioritized_tiles)

    # fill the first two rows with (8) tiles that are known to be new
    if request and request.GET.get('reqNum', 0) in [0, '0']:
        new_tiles = ir_created_last(tiles=tiles, exclude_set=exclude_set,
                                    allowed_set=allowed_set,
                                    results=num_new_tiles_to_autoprioritize)
        real_random.shuffle(new_tiles)
        prioritized_tiles += new_tiles

    if len(prioritized_tiles) >= results:
        return prioritized_tiles[:results]

    prioritized_tile_ids = ids_of(prioritized_tiles)

    # get (10 - number of prioritized) tiles that are not already prioritized
    random_tiles = ir_random(tiles=tiles,
                             results=(results - len(prioritized_tiles)),
                             exclude_set=prioritized_tile_ids,
                             allowed_set=allowed_set)

    tiles = prioritized_tiles + random_tiles
    return tiles[:results]


def ir_finite(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
              product_tiles_only=False, content_tiles_only=False,
              exclude_set=None, allowed_set=None, request=None,
              *args, **kwargs):
    """Return tiles in the following order:

    - prioritized ones (ordered by priority)
    - other ones (also ordered by priority)

    with no repeat.

    :param tiles: [<Tile>]
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
    prioritized_tiles += ir_priority_request(tiles=tiles, results=10,
                                             allowed_set=allowed_set)
    if len(prioritized_tiles) >= results:
        return prioritized_tiles[:results]

    # second, show the ones for the first request
    exclude_set += ids_of(prioritized_tiles)
    if request and request.GET.get('reqNum', 0) in [0, '0']:
        prioritized_tiles += ir_priority_pageview(tiles=tiles, results=10,
                                                  allowed_set=allowed_set)
    else:  # else... NEVER show these per-request tiles again
        x_prioritized_tiles = ir_priority_pageview(tiles=tiles, results=10,
                                                   allowed_set=allowed_set)
        exclude_set += ids_of(x_prioritized_tiles)
    if len(prioritized_tiles) >= results:
        return prioritized_tiles[:results]

    # fill the first two rows with (8) tiles that are known to be new
    exclude_set += ids_of(prioritized_tiles)
    if len(request.session.get('shown', [])) == 0:  # first page view
        prioritized_tiles += ir_created_last(tiles=tiles, results=8,
                                             exclude_set=exclude_set,
                                             allowed_set=allowed_set)
    if len(prioritized_tiles) >= results:
        return prioritized_tiles[:results]

    # get (10 - number of prioritized) tiles that are not already prioritized
    exclude_set += ids_of(prioritized_tiles)
    random_tiles = ir_prioritized(tiles=tiles, prioritized_set='',
        results=(results - len(prioritized_tiles)),
        exclude_set=exclude_set,
        allowed_set=allowed_set)

    real_random.shuffle(random_tiles)

    tiles = prioritized_tiles + random_tiles
    return tiles[:results]


def ir_finite_popular(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
    request=None, offset=0, *args, **kwargs):
    """Implements *exactly* the following goals:

    ... simpler code/algo, deterministic order and set of tiles (same on every pageview) ...
    ... sort by popularity ...

    Which means, if offset is not provided by the client, then the first 10
    will always be shown regardless of the number of requests made.
    """
    if results < 1:
        return []

    tiles = sorted(tiles, key=lambda tile: tile.click_score(), reverse=True)

    print "Returning popular tiles {0} through {1}".format(
        offset, offset + results)
    return tiles[offset:offset+results]  # all edge cases return []


def ir_finite_by(attribute='created_at', reversed_=False):
    """Returns a finite algorithm that orders its tiles based on a field,
    such as 'created_at'.

    Adding '-' will reverse the sort.
    """
    if attribute[0] == '-':
        attribute, reversed_ = attribute[1:], True

    @wraps(ir_finite_by)
    def algo(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
             request=None, offset=0, allowed_set=None, *args, **kwargs):
        """Outputs tiles, based on tiles' {attribute}, in offset slices."""
        def sort_fn(tile):
            """Turns a tile into a number"""
            try:
                sort_val = result(getattr(tile, attribute), arg=tile)
            except:
                sort_val = result(getattr(tile, attribute))
            return sort_val

        if results < 1:
            return []

        if allowed_set:
            tiles = tiles.filter(id__in=allowed_set)

        tiles = sorted(tiles, key=sort_fn, reverse=reversed_)

        # generate a verbose id:value map that shows exactly why a tile was
        # sorted this way
        tile_dump = "\n".join(
            ["{0}: {1}".format(tile.id, result(getattr(tile, attribute)))
             for tile in tiles][offset:offset+results])

        print "Returning popular tiles, by '{0}', {1} through {2}\n{3}".format(
            attribute, offset, offset + results, tile_dump)
        return tiles[offset:offset+results]  # all edge cases return []
    return algo


def ir_ordered(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
               product_tiles_only=False, content_tiles_only=False,
               exclude_set=None, allowed_set=None, request=None,
               *args, **kwargs):
    """Retrieve whichever finite tiles there are that have not been shown.
    If all have been shown, continue to show random ones.
    """
    tiles = ir_finite(tiles=tiles, results=results,
                      product_tiles_only=product_tiles_only,
                      content_tiles_only=content_tiles_only,
                      exclude_set=exclude_set, allowed_set=allowed_set,
                      request=request, **kwargs)
    if len(tiles) >= results:
        return tiles[:results]

    # get random tiles, with *no* exclusion restriction applied
    random_tiles = ir_prioritized(tiles=tiles, prioritized_set='',
        results=results, allowed_set=allowed_set)

    real_random.shuffle(random_tiles)
    tiles += random_tiles

    return tiles[:results]


def ir_related(tiles, tile_id, *args, **kwargs):
    """refactored from views. first parameter is unused."""
    from apps.assets.models import Tile
    return Tile.objects.get(id=tile_id).get_related()[:100]
