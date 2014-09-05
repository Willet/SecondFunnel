# coding=utf-8

"""Put all IR algorithms here. All algorithms must accept a <tiles>
as the first positional argument, with all other arguments being kwargs.

All algorithms must return <QuerySet>.
"""
import random
from functools import partial, wraps

from django.conf import settings
from django.db.models.query import QuerySet
from apps.assets.models import Tile
from apps.utils.functional import result, sort_helper


def ids_of(tiles):  # shorthand (got too annoying)
    return [getattr(tile, 'id') for tile in tiles]


def filter_tiles(fn):
    """Algorithm with this decorator receives a list of tiles that already
    have allowed_set and exclude_sets filtered.

    The algorithm will also be forced to return a QuerySet.
    """

    @wraps(fn)
    def wrapped_fn(*args, **kwargs):
        tiles, feed = kwargs.get('tiles'), kwargs.get('feed')
        allowed_set = kwargs.get('allowed_set')
        exclude_set = kwargs.get('exclude_set')

        results = kwargs.get('results', 10)

        content_only = kwargs.get('content_only', False)
        products_only = kwargs.get('products_only', False)

        if not feed and tiles is None:  # permit [] for tiles
            raise ValueError("Either tiles or feed must be supplied")

        if not tiles and feed:
            tiles = feed.tiles.all()

        if not tiles:  # nothing to give
            return qs_for([])

        if results < 1:  # nothing to get
            return qs_for([])

        if not isinstance(tiles, QuerySet):
            tiles = qs_for(tiles)

        tiles = filter_excluded(tiles, allowed_set, exclude_set)
        if products_only:
            tiles = tiles.filter(template='product')
        if content_only:
            tiles = tiles.exclude(template='product')

        kwargs.update({
            'tiles': tiles,
        })
        tiles = fn(*args, **kwargs)

        if not isinstance(tiles, QuerySet):
            tiles = qs_for(tiles)

        return tiles

    return wrapped_fn


def returns_qs(fn):
    """Algorithms with this decorator will always return a QuerySet."""

    @wraps(fn)
    def wrapped_fn(*args, **kwargs):
        tiles, feed = kwargs.pop('tiles'), kwargs.get('feed')
        if feed:
            tiles = feed.tiles.all()

        content_only = kwargs.get('content_only', False)
        products_only = kwargs.get('products_only', False)
        if products_only:
            tiles = tiles.filter(template='product')
        if content_only:
            tiles = tiles.exclude(template='product')

        kwargs.update({'tiles': tiles})

        tiles = fn(*args, **kwargs)

        if not isinstance(tiles, QuerySet):
            tiles = qs_for(tiles)

        return tiles

    return wrapped_fn


def filter_excluded(tiles, allowed_set=None, exclude_set=None):
    """Given a Tile QuerySet, apply allowed_set and/or exclude_set to it
    if present.
    """
    if allowed_set:
        tiles = tiles.filter(id__in=allowed_set)
    if exclude_set:
        tiles = tiles.exclude(id__in=exclude_set)
    return tiles


def qs_for(tiles):
    """Convert a list of tiles to a queryset containing those tiles.

    Executes at least one query.

    :returns {QuerySet}
    """
    if isinstance(tiles, QuerySet):
        return tiles

    if not tiles:
        tiles = []

    # raw SQL for obtaining a queryset the with the same order as the input set
    # blog.mathieu-leplatre.info/django-create-a-queryset-from-a-list-preserving-order.html
    # (large-set testing required)
    pk_list = [x.pk for x in tiles]
    clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i)
                        for i, pk in enumerate(pk_list)])
    ordering = 'CASE %s END' % clauses
    qs = Tile.objects.filter(pk__in=pk_list).extra(
        select={'ordering': ordering},
        order_by=('ordering', ))

    return qs


def directional(fn):
    """Given a dynamic sort algorithm like ir_finite_by_(any), Automatically
    detect whether its sort is reversed.
    """
    @wraps(fn)
    def wrapped(attribute, reversed_=False):
        """If the attribute begins with '-', the sort will be reversed."""
        if attribute[0] == '-':
            attribute, reversed_ = attribute[1:], True
        return fn(attribute=attribute, reversed_=reversed_)
    return wrapped


@filter_tiles
def ir_base(tiles=None, feed=None, exclude_set=None, allowed_set=None,
            **kwargs):
    """Common algo for removes tiles that no IR algorithm will ever serve.

    Required parameters: either tiles (list / QuerSet) or feed (<Feed>)
    If allowed_set and exclude_set are given, then the resultant queryset will
    include and exclude these tiles, respectively, if a feed is given as well.

    returns {QuerySet} of {Tile} instances (which is *not* a list)
    """

    # "filter out all content tiles for which none of the content's
    # tagged products are in stock"
    tiles = (tiles.exclude(products__in_stock=False)
             .exclude(content__tagged_products__in_stock=False))

    # DO NOT call *_related functions after ir_base!
    return tiles


def ir_all(tiles, *args, **kwargs):
    return tiles


@filter_tiles
def ir_first(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
             allowed_set=None, exclude_set=None, *args, **kwargs):
    """sample whichever ones come first"""
    # serve prioritized ones first
    prioritized_tiles = tiles.exclude(prioritized='').order_by('updated_at')

    if len(prioritized_tiles) >= results:
        return prioritized_tiles

    prioritized_tiles = list(prioritized_tiles)
    return prioritized_tiles + list(tiles.order_by('id'))[:results]


@returns_qs
def ir_last(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
            allowed_set=None, *args, **kwargs):
    """sample whichever ones come last"""
    if results < 1:
        return []

    return tiles.order_by('-id')[:results]


@filter_tiles
def ir_prioritized(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                   prioritized_set='', exclude_set=None, allowed_set=None,
                   **kwargs):
    """Return prioritized tiles in the feed, ordered by priority,
    except the ones in exclude_set, which is a list of old id integers.
    """
    tiles = (tiles.filter(prioritized=prioritized_set)
             .order_by('-priority', '?')[:results])

    print "{0} tile(s) were manually prioritized by {1}".format(
        len(tiles), prioritized_set or 'nothing')

    return tiles


ir_priority_request = partial(ir_prioritized, prioritized_set='request')
ir_priority_pageview = partial(ir_prioritized, prioritized_set='pageview')
ir_priority_session = partial(ir_prioritized, prioritized_set='session')
ir_priority_cookie = partial(ir_prioritized, prioritized_set='cookie')
ir_priority_custom = partial(ir_prioritized, prioritized_set='custom')


@filter_tiles
def ir_priority_sorted(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                       prioritized_state='any', exclude_set=None,
                       allowed_set=None, **kwargs):
    """Return prioritized tiles in the feed, ordered by their priority values,
    except the ones in exclude_set, which is a list of id integers.
    """
    tiles = tiles.filter(prioritized=prioritized_state) \
                .order_by('-priority')[:results]

    print "{0} tile(s) were manually prioritized".format(len(tiles))
    return tiles


@filter_tiles
def ir_random(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS, **kwargs):
    """get (a numbr of) random tiles, except the ones in exclude_set,
    which is a list of old id integers."""
    if not tiles and kwargs.pop("exclude_set"):
        tiles = ir_random(**kwargs)

    tiles = list(tiles)
    random.shuffle(tiles)

    tiles = tiles[:results]

    print "{0} tile(s) were randomly added".format(len(tiles))

    return tiles


@filter_tiles
def ir_created_last(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                    exclude_set=None, allowed_set=None, *args, **kwargs):
    """Return most recently-created tiles in the feed, except the ones in
    exclude_set, which is a list of old id integers.
    """
    tiles = tiles.order_by("-created_at", "?")[:results]

    print "{0} tile(s) were automatically prioritized by -created".format(len(tiles))
    return tiles


@filter_tiles
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
    tiles = tiles.order_by('-clicks')
    return tiles[:results]


@returns_qs
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

    with no repeat per request.

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
    if request and int(request.GET.get('reqNum', 0)) == 0:
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
    if request and request.GET.get('reqNum', '0') == '0':
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
                             allowed_set=allowed_set,
                             feed=kwargs.get('feed', None))

    tiles = list(prioritized_tiles) + list(random_tiles)
    return tiles[:results]


@returns_qs
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
    prioritized_tiles = []
    if not (request and hasattr(request, 'session')):
        raise ValueError("Sessions must be enabled for ir_ordered")

    # first, always show the ones that are 'request' i.e. every request
    prioritized_tiles += ir_priority_request(tiles=tiles, results=10,
                                             allowed_set=allowed_set)
    if len(prioritized_tiles) >= results:
        return prioritized_tiles[:results]

    # second, show the ones for the first request
    exclude_set += ids_of(prioritized_tiles)
    if request and request.GET.get('reqNum', '0') == '0':
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
                                  allowed_set=allowed_set,
                                  feed=kwargs.get('feed', None))

    tiles = list(prioritized_tiles) + list(random_tiles)
    return tiles[:results]


@filter_tiles
def ir_finite_popular(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                      request=None, offset=0, allowed_set=None, exclude_set=None, *args, **kwargs):
    """Implements *exactly* the following goals:

    ... simpler code/algo, deterministic order and set of tiles (same on every pageview) ...
    ... sort by popularity ...

    Which means, if offset is not provided by the client, then the first 10
    will always be shown regardless of the number of requests made.
    """
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
        return tiles[offset:offset + results]


@returns_qs
def ir_mixed(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
             exclude_set=None, allowed_set=None, request=None,
             feed=None, *args, **kwargs):
    """Returns tiles, a mix of content and products in a ratio set
        in the admin (feed_ratio). The tiles are randomly mixed in each
        request so that they do not return as content -> products

        This algorithm support prioritization by pageview and no other methods of prioritization.

    :param tiles: [<Tile>]
    :param results: int (number of results you want)
    :param exclude_set: <list<int>> do not return tiles with these ids.
    :param request: if supplied, do not return results used in
                    the previous session call, or tile ids specified by the
                    "?shown=" parameter.
    :param feed: used to determine the feed_ratio for this product/content
                 feed. feed_ratio defaults to 0.2 if not supplied.
    :returns list
    """

    # check for sessions
    if not (request and hasattr(request, 'session')):
        raise ValueError("Sessions must be enabled for ir_mixed")

    if results < 1:
        return []

    percentage_content = 0.2
    if feed:
        percentage_content = float(feed.feed_ratio)
    percentage_product = 1 - percentage_content
    # round up and down by adding 0.5. thus correct number of products and content
    num_content = int((results * percentage_content) + 0.5)
    num_product = int((results * percentage_product) + 0.5)

    contents = tiles.exclude(template='product')
    products = tiles.filter(template='product')

    exclude_set = set(exclude_set)
    print "exclude set size is {}".format(len(exclude_set))

    # if all tiles have been used, reset and start again
    # reset content views when all content ids are present in exclude_set
    if set(ids_of(contents)).issubset(exclude_set):
        print "Ran out of contents: resetting"
        exclude_set = exclude_set - set(ids_of(contents))
        request.session['shown'] = list(exclude_set)

    # reset product views when all product ids are present in exclude_set
    if set(ids_of(products)).issubset(exclude_set):
        # print "Ran out of products: resetting"  # this almost never happens
        exclude_set = exclude_set - set(ids_of(products))
        request.session['shown'] = list(exclude_set)

    products = products.exclude(id__in=exclude_set)
    contents = contents.exclude(id__in=exclude_set)

    # only at start, this allows for *all* prioritized tiles so this algo
    # doesn't have to worry about them after request 0.
    # prior to this change, the algo returns strictly 5 products or 5 contents
    # even when only contents are prioritized, which means prioritized results
    # are mixed with non-prioritized ones.
    if request and str(request.GET.get('reqNum', '0')) == '0':
        prioritized_tiles = ir_priority_pageview(tiles=tiles, results=1000,
            exclude_set=exclude_set, allowed_set=allowed_set)
        if prioritized_tiles:
            print "returning {} prioritized tiles".format(prioritized_tiles.count())
            return prioritized_tiles

    contents = list(contents.order_by('-clicks')[:num_content])
    products = list(products.order_by('-priority')[:num_product])

    tiles = contents + products

    rnp, rnc = len(products[:num_product]), len(contents[:num_content])
    random.shuffle(tiles)  # shuffles in place, returns None

    print "returning tiles {} ({} product, {} content)".format(
        ','.join([str(t.id) for t in tiles]), rnp, rnc)

    if len(tiles) > results:
        return tiles[:results]
    return tiles


@returns_qs
def ir_content_first(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                     exclude_set=None, allowed_set=None, request=None,
                     *args, **kwargs):
    """Return tiles in the following order:

    - prioritized content
    - products mixed with content (ir_mixed)

    Calls same functions as ir_finite with content only,
    then calls ir_mixed when all content has been used

    :param tiles: [<Tile>]
    :param results: int (number of results you want)
    :param exclude_set: <list<int>> do not return tiles with these ids.
    :param request: if supplied, do not return results used in
                    the previous session call, or tile ids specified by the
                    "?shown=" parameter.
    :returns list
    """

    # check for sessions
    if not (request and hasattr(request, 'session')):
        raise ValueError("Sessions must be enabled for ir_content_first")

    if results < 1:
        return []

    # since contents first is all about contents, we don't need to worry
    # about products. ir_mixed will handle that if necessary
    contents = tiles.exclude(template='product')

    prioritized_content = []

    # first, always show the ones that are 'request' i.e. every request
    prioritized_content += ir_priority_request(tiles=contents, results=10,
                                               exclude_set=exclude_set, allowed_set=allowed_set)
    if len(prioritized_content) >= results:
        return prioritized_content[:results]

    # second, show the ones for the first request
    exclude_set += ids_of(prioritized_content)
    if request and request.GET.get('reqNum', '0') in ['0', '1']:  # only at start, this allows for 20 tiles
        prioritized_content += ir_priority_pageview(tiles=contents, results=results,
                                                    exclude_set=exclude_set, allowed_set=allowed_set)

    length = len(prioritized_content)

    if length >= results:
        return prioritized_content[:results]

    exclude_set += ids_of(prioritized_content)
    mixed_tiles = ir_mixed(tiles=tiles, results=(results - length),
                           exclude_set=exclude_set, allowed_set=allowed_set,
                           request=request, feed=kwargs.get('feed', None))
    prioritized_content += mixed_tiles

    return prioritized_content[:results]


@directional
def ir_finite_by(attribute='created_at', reversed_=False):
    """Returns a finite algorithm that orders its tiles based on a field,
    such as 'created_at'.

    Adding '-' will reverse the sort.
    """

    @wraps(ir_finite_by)
    @returns_qs
    def algo(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
             request=None, offset=0, allowed_set=None, exclude_set=None,
             *args, **kwargs):
        """Outputs tiles, based on tiles' {attribute}, in offset slices."""

        if results < 1:
            return []

        tiles = filter_excluded(tiles, allowed_set, exclude_set)

        sort_fn = partial(sort_helper, attribute=attribute)
        tiles = sorted(tiles, key=sort_fn, reverse=reversed_)

        # generate a verbose id:value map that shows exactly why a tile was
        # sorted this way
        tile_dump = "\n".join(
            ["{0}: {1}".format(tile.id, result(getattr(tile, attribute)))
             for tile in tiles][:results])

        print "Returning popular tiles, by '{0}', " \
              "emulating offset {1} ~ {2}\n{3}".format(attribute, offset, offset + results, tile_dump)

        # all edge cases return []
        if exclude_set or allowed_set:
            # if exclude set is supplied, then the top 10 results should
            # already be the results you should show next
            return tiles[:results]
        else:
            return tiles[offset:offset + results]

    return algo


@returns_qs
def ir_auto(tiles, request=None, *args, **kwargs):
    """
    Using a laughable number of queries, return the "best" algorithm for
    displaying a feed.
    """
    finite = False
    if request:
        finite = (len(request.session.get('shown', [])) > 0)

    product_count = len([t for t in tiles if t.template == 'product'])
    content_count = len([t for t in tiles if t.template != 'product'])

    # because we want to see more content than more products, this is an
    # undesirable situation to be in -- use infinite algorithms instead
    if product_count > content_count:
        if content_count < 5:
            return ir_ordered(tiles=tiles, *args, **kwargs)

        # how large is the sample space?
        if len(tiles) < 100:
            return ir_generic(tiles=tiles, *args, **kwargs)
        return ir_random(tiles=tiles, *args, **kwargs)

    # how much engagement can we detect?
    views_count = sum([t.views for t in tiles])
    clicks_count = sum([t.clicks for t in tiles])
    if clicks_count > 100:
        if finite:
            return ir_finite_popular(tiles=tiles, *args, **kwargs)
        else:
            return ir_popular(tiles=tiles, *args, **kwargs)
    elif views_count > 1000:
        return ir_finite_by('-views')(tiles=tiles, *args, **kwargs)

    # wild guess mode?
    if not finite:
        kwargs['exclude_set'] = []
    return ir_random(tiles=tiles, *args, **kwargs)


@returns_qs
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

    # this is causing problems on master with sorting already-sliced querysets
    # -- can anyone else confirm?
    # random_tiles = random_tiles.order_by('?')
    tiles = list(tiles) + list(random_tiles)

    return tiles[:results]


@directional
def ir_ordered_by(attribute='created_at', reversed_=False):
    """Returns a ordered algorithm that orders its tiles based on a field,
    such as 'created_at'.

    Adding '-' will reverse the sort.
    """
    @wraps(ir_ordered_by)
    @returns_qs
    def algo(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
             request=None, offset=0, allowed_set=None, exclude_set=None,
             *args, **kwargs):
        """Outputs tiles, based on tiles' {attribute}, in offset slices.
        If no more tiles are left in the offset, the offset is reset relative
        to the total size of the tile pool and looped back again to the head.
        """
        if results < 1:
            return []

        # "or tiles" forces tiles to reset when
        # tile pool is very small (think nastygal)
        tiles = filter_excluded(tiles, allowed_set, exclude_set) or tiles

        sort_fn = partial(sort_helper, attribute=attribute)
        tiles = sorted(tiles, key=sort_fn, reverse=reversed_)
        tile_count = len(tiles)

        # loop offsets
        if tile_count:
            offset = offset % tile_count
        else:
            offset = 0
        tiles = tiles[offset:offset + results]

        return tiles

    return algo


@filter_tiles
def ir_finite_sale(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                   offset=0, allowed_set=None, exclude_set=None,
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

        discounts = [
            parse_int(
                product.attributes.get('discount', product.attributes.get('sale_price', 0))
            ) for product in products
        ]
        if discounts:
            max_sale = max(discounts)
        else:
            max_sale = 0  # no discount = no sale
        return max_sale

    tiles = sorted(tiles, key=sort_fn, reverse=True)

    print "Returning discounted product tiles, " \
          "emulating offset {0} ~ {1}".format(offset, offset + results)

    # all edge cases return []
    if exclude_set or allowed_set:
        # if exclude set is supplied, then the top 10 results should
        # already be the results you should show next
        return tiles[:results]
    else:
        return tiles[offset:offset + results]
