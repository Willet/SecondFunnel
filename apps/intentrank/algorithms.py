# coding=utf-8

"""Put all IR algorithms here. All algorithms must accept a <tiles>
as the first positional argument, with all other arguments being kwargs.

All algorithms must return <list>.
"""
from functools import partial, wraps

from django.conf import settings
from django.db.models.query import QuerySet
from apps.assets.models import Tile
from apps.utils.functional import result
from secondfunnel.errors import deprecated


def ids_of(tiles):  # shorthand (got too annoying)
    return [getattr(tile, 'old_id', getattr(tile, 'id')) for tile in tiles]


def qs_for(tiles):
    """Convert a list of tiles to a queryset containing those tiles.

    Executes at least one query.

    :returns {QuerySet}
    """
    if isinstance(tiles, QuerySet):
        return tiles

    try:
        ids = [x.id for x in tiles]
    except AttributeError as err:
        ids = tiles

    return (Tile.objects.filter(id__in=ids)
                .prefetch_related(*Tile.ASSOCS)
                .select_related(*Tile.ASSOCS))


def ir_base(tiles=None, feed=None, exclude_set=None, allowed_set=None,
            **kwargs):
    """Common algo for removes tiles that no IR algorithm will ever serve.

    Required parameters: either tiles (list / QuerSet) or feed (<Feed>)
    If allowed_set and exclude_set are given, then the resultant queryset will
    include and exclude these tiles, respectively, if a feed is given as well.

    returns {QuerySet} of {Tile} instances (which is *not* a list)
    """
    if not feed and tiles is None:  # permit [] for tiles
        raise ValueError("Either tiles or feed must be supplied to ir_base")

    if feed:
        tiles = feed.get_tiles()

    if not isinstance(tiles, QuerySet):
        tiles = qs_for(tiles)

    if allowed_set:
        tiles = tiles.filter(id__in=allowed_set)

    if exclude_set:
        tiles = tiles.exclude(id__in=exclude_set)

    # "filter out all content tiles for which none of the content's
    # tagged products are in stock"
    tiles = (tiles.exclude(products__in_stock=False)
                  .exclude(content__tagged_products__in_stock=False))

    # DO NOT call *_related functions after ir_base!
    return tiles


def ir_all(tiles, *args, **kwargs):
    return tiles


def ir_first(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
             allowed_set=None, exclude_set=None, *args, **kwargs):
    """sample whichever ones come first"""
    # serve prioritized ones first
    if results < 1:
        return []

    if allowed_set:
        tiles = tiles.filter(id__in=allowed_set)
    if exclude_set:
        tiles = tiles.exclude(id__in=exclude_set)

    prioritized_tiles = tiles.exclude(prioritized='').order_by('updated_at')

    if len(prioritized_tiles) >= results:
        return prioritized_tiles

    prioritized_tiles = list(prioritized_tiles)
    return qs_for(prioritized_tiles + list(tiles.order_by('id')))[:results]


def ir_last(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
            allowed_set=None, *args, **kwargs):
    """sample whichever ones come last"""
    if results < 1:
        return []

    return tiles.order_by('-id')[:results]


def ir_prioritized(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                   prioritized_set='', exclude_set=None, allowed_set=None,
                   **kwargs):
    """Return prioritized tiles in the feed, ordered by priority,
    except the ones in exclude_set, which is a list of old id integers.
    """
    if results < 1:
        return []

    if allowed_set:
        tiles = tiles.filter(id__in=allowed_set)
    if exclude_set:
        tiles = tiles.exclude(id__in=exclude_set)

    tiles = tiles.filter(prioritized=prioritized_set)

    tiles = tiles.order_by('-priority', '?')[:results]

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

    if allowed_set:
        tiles = tiles.filter(id__in=allowed_set)
    if exclude_set:
        tiles = tiles.exclude(id__in=exclude_set)

    tiles = tiles.filter(prioritized=prioritized_state)\
                 .order_by('-priority')[:results]

    print "{0} tile(s) were manually prioritized".format(len(tiles))
    return tiles


def ir_random(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
              exclude_set=None, allowed_set=None, **kwargs):
    """get (a numbr of) random tiles, except the ones in exclude_set,
    which is a list of old id integers."""
    if results < 1:
        return []

    if allowed_set:
        tiles = tiles.filter(id__in=allowed_set)
    if exclude_set:
        tiles = tiles.exclude(id__in=exclude_set)

    tiles = tiles.order_by('?')
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

    if allowed_set:
        tiles = tiles.filter(id__in=allowed_set)
    if exclude_set:
        tiles = tiles.exclude(id__in=exclude_set)

    tiles = tiles.order_by("-created_at", "?")[:results]

    print "{0} tile(s) were automatically prioritized by -created".format(len(tiles))
    return tiles


def ir_popular(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
               request=None, exclude_set=None, allowed_set=None,
               *args, **kwargs):
    """Sample without replacement
    returns tiles with a higher chance for a tile to be returned if it is a popular tile

    :param tiles: [Tile]
    :param results: int (number of results you want)
    :param exclude_set: <list<int>> do not return tiles with these ids.
    :param request: if supplied, do not return results used in
                    the previous session call, or tile ids specified by the
                    "?shown=" parameter.
    :returns list
    """
    if results < 1:
        return []

    tiles = tiles.order_by('-clicks')

    if allowed_set:
        tiles = tiles.filter(id__in=allowed_set)
    if exclude_set:
        tiles = tiles.exclude(id__in=exclude_set)

    return tiles[:results]


def ir_generic(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
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
    exclude_set += ids_of(prioritized_tiles)

    # second, show the ones for the first request
    if request and request.GET.get('reqNum', 0) in [0, '0']:
        prioritized_tiles += ir_priority_pageview(tiles=tiles, results=10,
                                                  exclude_set=exclude_set,
                                                  allowed_set=allowed_set)
        exclude_set += ids_of(prioritized_tiles)

    if len(prioritized_tiles) >= results:
        return prioritized_tiles[:results]

    # third, show the ones that have never been shown in this session
    if request and hasattr(request, 'session'):
        if len(request.session.get('shown', [])) == 0:  # first page view
            prioritized_tiles += ir_priority_session(tiles=tiles, results=8,
                exclude_set=exclude_set,
                allowed_set=allowed_set)
            exclude_set += ids_of(prioritized_tiles)

    # fill the first two rows with (8) tiles that are known to be new
    if request and request.GET.get('reqNum', 0) in [0, '0']:
        new_tiles = ir_created_last(tiles=tiles, exclude_set=exclude_set,
                                    allowed_set=allowed_set,
                                    results=num_new_tiles_to_autoprioritize)
        prioritized_tiles += new_tiles

    if len(prioritized_tiles) >= results:
        return prioritized_tiles[:results]

    prioritized_tile_ids = ids_of(prioritized_tiles)

    # get (10 - number of prioritized) tiles that are not already prioritized
    random_tiles = ir_random(tiles=tiles,
                             results=(results - len(prioritized_tiles)),
                             exclude_set=prioritized_tile_ids,
                             allowed_set=allowed_set)

    tiles = list(prioritized_tiles) + list(random_tiles)
    return qs_for(tiles[:results])


def ir_finite(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
              exclude_set=None, allowed_set=None, request=None,
              *args, **kwargs):
    """Return tiles in the following order:

    - prioritized ones (ordered by priority)
    - other ones (also ordered by priority)

    with no repeat.

    :param tiles: [<Tile>]
    :param results: int (number of results you want)
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

    tiles = list(prioritized_tiles) + list(random_tiles)
    return tiles[:results]


def ir_finite_popular(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
    request=None, offset=0, allowed_set=None, exclude_set=None, *args, **kwargs):
    """Implements *exactly* the following goals:

    ... simpler code/algo, deterministic order and set of tiles (same on every pageview) ...
    ... sort by popularity ...

    Which means, if offset is not provided by the client, then the first 10
    will always be shown regardless of the number of requests made.
    """
    if results < 1:
        return []

    if allowed_set:
        tiles = tiles.filter(id__in=allowed_set)

    if exclude_set:
        tiles = tiles.exclude(id__in=exclude_set)

    tiles = tiles.extra(select={
        'clicks_per_view': 'cast(clicks + 1 as float) / cast(views + 1 as float)'
    }).order_by('-clicks_per_view')

    print "Returning popular tiles {0} through {1}".format(
        offset, offset + results)

    # all edge cases return []
    if exclude_set or allowed_set:
        # if exclude set is supplied, then the top 10 results should
        # already be the results you should show next
        return tiles[:results]
    else:
        return tiles[offset:offset+results]


def ir_mixed(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
             exclude_set=None, allowed_set=None, request=None,
             *args, **kwargs):

    PERCENTAGE_CONTENT = 0.6
    PERCENTAGE_PRODUCT = 1 - PERCENTAGE_CONTENT

    if results < 1:
        return []

    print "ir_mixed called"

    contents_temp = tiles.exclude(template='product')
    products_temp = tiles.filter(template='product')

    if len(exclude_set) >= len(tiles):
        print "exclude_set reset"
        exclude_set = None

    if len(tiles.filter(id__in=exclude_set).exclude(template='product')) >= len(contents_temp):
        print "exclude_set - contents"
        for x in ids_of(contents_temp):
            exclude_set.remove(x)

    if len(tiles.filter(id__in=exclude_set).filter(template='product')) >= len(products_temp):
        print "exclude_set - contents"
        for x in ids_of(products_temp):
            exclude_set.remove(x)

    if allowed_set:
        tiles = tiles.filter(id__in=allowed_set)
    if exclude_set:
        tiles = tiles.exclude(id__in=exclude_set)

    products = tiles.filter(template='product')
    contents = tiles.exclude(template='product')

    num_content = int(results * PERCENTAGE_CONTENT)
    num_product = int(results * PERCENTAGE_PRODUCT)

    contents = contents.order_by('-clicks')[:num_content]

    products = products.order_by('-priority')[:num_product]

    tiles = list(contents) + list(products)

    print "products: {0} and content: {1}".format(len(products[:num_product]),
                                                  len(contents[:num_content]))
    return qs_for(tiles).order_by('?')


def ir_content_first(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                       exclude_set=None, allowed_set=None, request=None,
                       *args, **kwargs):
    """Return tiles in the following order:

    - prioritized content (ordered by priority)
    - products mixed mixed with content

    Calls same functions as ir_finite with content only,
    then calls ir_mixed when all content has been used

    :param new_tiles: [<Tile>]
    :param results: int (number of results you want)
    :param exclude_set: <list<int>> do not return tiles with these ids.
    :param request: if supplied, do not return results used in
                    the previous session call, or tile ids specified by the
                    "?shown=" parameter.
    :returns list
    """

    if results < 1:
        return []

    if request and request.GET.get('IRReqNum', 2):
        print "product mix starting"
        mixed_tiles = ir_mixed(tiles=tiles, results=results,
                               exclude_set=exclude_set, allowed_set=allowed_set)
        return mixed_tiles[:results]

    contents = tiles.exclude(template='product')

    print "content_first run"

    # check for sessions
    if not (request and hasattr(request, 'session')):
        raise ValueError("Sessions must be enabled for ir_ordered")

    prioritized_content = []

    # first, always show the ones that are 'request' i.e. every request
    prioritized_content += ir_priority_request(tiles=tiles, results=10,
                                               allowed_set=allowed_set)
    if len(prioritized_content) >= results:
        return prioritized_content[:results]

    # serve prioritized ones first
    # second, show the ones for the first request
    exclude_set += ids_of(prioritized_content)
    if request and request.GET.get('reqNum', 0) in [0, '0']:
        prioritized_content += ir_priority_pageview(tiles=contents, results=10,
                                                    allowed_set=allowed_set)

    if len(prioritized_content) >= results:
        print "step two returned"
        return prioritized_content[:results]

    # fill the first two rows with (8) tiles that are known to be new

    exclude_set += ids_of(prioritized_content)
    if len(request.session.get('shown', [])) == 0:  # first page view
        prioritized_content += ir_created_last(tiles=contents, results=8,
                                               exclude_set=exclude_set,
                                               allowed_set=allowed_set)

    if len(prioritized_content) >= results:
        print "step three returned"
        return prioritized_content[:results]

    random_content = []
    exclude_set += ids_of(prioritized_content)
    # get (10 - number of prioritized) tiles that are not already prioritized
    if not len(contents) <= len(exclude_set):
        random_content = ir_prioritized(tiles=contents, prioritized_set='',  # the rest of the contents
                                        results=(results - len(prioritized_content)),
                                        exclude_set=exclude_set,
                                        allowed_set=allowed_set)

    new_tiles = list(prioritized_content) + list(random_content)

    length = len(random_content) + len(prioritized_content)
    if length >= results:
        print "step four random content returned"
        return new_tiles[:results]

    mixed_tiles = ir_mixed(tiles=tiles, results=(results - length),
                           exclude_set=exclude_set, allowed_set=allowed_set)
    new_tiles += list(mixed_tiles)
    print "step four returned"
    return new_tiles[:results]

def ir_finite_by(attribute='created_at', reversed_=False):
    """Returns a finite algorithm that orders its tiles based on a field,
    such as 'created_at'.

    Adding '-' will reverse the sort.
    """
    if attribute[0] == '-':
        attribute, reversed_ = attribute[1:], True

    @wraps(ir_finite_by)
    def algo(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
             request=None, offset=0, allowed_set=None, exclude_set=None,
             *args, **kwargs):
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

        if exclude_set:
            tiles = tiles.exclude(id__in=exclude_set)

        tiles = sorted(tiles, key=sort_fn, reverse=reversed_)

        # generate a verbose id:value map that shows exactly why a tile was
        # sorted this way
        tile_dump = "\n".join(
            ["{0}: {1}".format(tile.id, result(getattr(tile, attribute)))
             for tile in tiles][:results])

        print "Returning popular tiles, by '{0}', " \
              "emulating offset {1} ~ {2}\n{3}".format(
            attribute, offset, offset + results, tile_dump)

        # all edge cases return []
        if exclude_set or allowed_set:
            # if exclude set is supplied, then the top 10 results should
            # already be the results you should show next
            return tiles[:results]
        else:
            return tiles[offset:offset+results]
    return algo


def ir_auto(tiles, *args, **kwargs):
    """
    Using a laughable number of queries, return the "best" algorithm for
    displaying a feed.
    """
    finite = False
    request = kwargs.get('request', None)
    if request:
        finite = (len(request.session.get('shown', [])) > 0)

    product_count = len([t for t in tiles if t.template == 'product'])
    content_count = len([t for t in tiles if t.template != 'product'])

    # because we want to see more content than more products, this is an
    # undesirable situation to be in -- use infinite algorithms instead
    if product_count > content_count:
        if content_count < 5:
            return ir_ordered(tiles, *args, **kwargs)

        # how large is the sample space?
        if len(tiles) < 100:
            return ir_generic(tiles, *args, **kwargs)
        return ir_random(tiles, *args, **kwargs)

    # how much engagement can we detect?
    views_count = sum([t.views for t in tiles])
    clicks_count = sum([t.clicks for t in tiles])
    if clicks_count > 100:
        if finite:
            return ir_finite_popular(tiles, *args, **kwargs)
        else:
            return ir_popular(tiles, *args, **kwargs)
    elif views_count > 1000:
        return ir_finite_by('-views')(tiles, *args, **kwargs)

    # wild guess mode?
    if not finite:
        kwargs['exclude_set'] = []
    return ir_random(tiles, *args, **kwargs)


def ir_ordered(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
               exclude_set=None, allowed_set=None, request=None,
               *args, **kwargs):
    """Retrieve whichever finite tiles there are that have not been shown.
    If all have been shown, continue to show random ones.
    """
    tiles = ir_finite(tiles=tiles, results=results,
                      exclude_set=exclude_set, allowed_set=allowed_set,
                      request=request, **kwargs)
    if len(tiles) >= results:
        return tiles[:results]

    # get random tiles, with *no* exclusion restriction applied
    random_tiles = ir_prioritized(tiles=tiles, prioritized_set='',
        results=results, allowed_set=allowed_set)

    random_tiles = random_tiles.order_by('?')
    tiles += random_tiles

    return tiles[:results]


def ir_finite_sale(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
         request=None, offset=0, allowed_set=None, exclude_set=None,
         *args, **kwargs):
    """Outputs tiles, based on tiles' products' discount, in offset slices."""
    def sort_fn(tile):
        """Turns a tile into a number"""
        def parse_int(string):
            if not string:
                return 0
            return int(''.join([x for x in string if x.isdigit()]))

        products = list(tile.products.all())
        for content in tile.content.all():
            products.extend(list(content.tagged_products.all()))

        max_sale = max([parse_int(product.attributes.get('discount',
                                   product.attributes.get('sale_price', 0)))
                        for product in products])
        return max_sale

    if results < 1:
        return []

    if allowed_set:
        tiles = tiles.filter(id__in=allowed_set)

    if exclude_set:
        tiles = tiles.exclude(id__in=exclude_set)

    tiles = sorted(tiles, key=sort_fn, reverse=True)

    print "Returning discounted product tiles, " \
          "emulating offset {0} ~ {1}".format(offset, offset + results)

    # all edge cases return []
    if exclude_set or allowed_set:
        # if exclude set is supplied, then the top 10 results should
        # already be the results you should show next
        return tiles[:results]
    else:
        return tiles[offset:offset+results]
