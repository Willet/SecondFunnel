# coding=utf-8

"""Put all IR algorithms here. All algorithms must accept a <tiles>
as the first positional argument, with all other arguments being kwargs.

All algorithms must return <QuerySet>.
"""
import random
from functools import partial, wraps

from django.conf import settings
from django.db.models import Count
from django.db.models.query import QuerySet
from apps.assets.models import Tile


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

        if tiles is None and feed:
            tiles = feed.tiles.all()
        if not tiles:  # nothing to give
            return qs_for([])

        if results < 1:  # nothing to get
            return qs_for([])

        if not isinstance(tiles, QuerySet):
            tiles = qs_for(tiles)

        tiles = filter_excluded(tiles, allowed_set, exclude_set)
        # Banner tiles are special tiles meant to link elsewhere
        # Force them into all feeds
        if products_only:
            tiles = tiles.filter(template__in=['product','banner'])
        if content_only:
            tiles = tiles.exclude(template__in=['product','banner'])

        kwargs.update({
            'tiles': tiles,
        })
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


def ir_magic(tiles, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
             offset=0, feed=None, page=None, *args, **kwargs):
    """
    1. Tiles can be finite or infinite
    2. Any two tiles with an identical priority value can be ordered randomly
    3. Any two content of types that are automatically in motion (ex: gif, not youtube) 
       must be apart from each other
    4. product/content ratio must be customizable BUT if available products/contents 
       count is above or beyond an "reasonable" value, then do not obey product/content ratio
    5. In no situation will algorithm attempt to repeat its content until necessary
    """

    # Getting the template types in this feed
    template_types = tiles.distinct('template').values_list('template', flat=True)

    # Make sure we do not have any duplicates
    tiles = tiles.distinct('id', 'priority')

    total_tiles = tiles.count()
    if total_tiles == 0:
        return tiles

    # This feed is finite and has returned all of the tiles
    if feed and feed.is_finite and offset >= total_tiles and not (page and page.theme_settings.get('override_finite_feed', False)):
        return qs_for([])

    # Wrapping results
    overflow = results - total_tiles % results
    if results == overflow:
        overflow = 0

    while offset >= total_tiles:
        offset -= overflow + total_tiles

    templated_tiles = {}

    for template_type in template_types:
        tile_list = list(tiles.filter(template=template_type).order_by('-priority'))
        total = len(tile_list)

        templated_tiles[template_type] = {
            'tiles': tile_list,
            'total': total,
            'ratio': total / float(total_tiles),
            'added': 0,
        }

    result_tiles = []

    def get_next_tile():
        tile_list = []
        highest_priority = 0
        worst_ratio = 2

        # Pick the tile(s) with the highest priority
        for _, templated_tile in templated_tiles.iteritems():
            if templated_tile['added'] < templated_tile['total']:
                tile_candidate = templated_tile['tiles'][templated_tile['added']]

                if tile_candidate.priority > highest_priority:
                    tile_list = [tile_candidate]
                    highest_priority = tile_candidate.priority
                elif tile_candidate.priority == highest_priority:
                    tile_list.append(tile_candidate)

        # Pick the tile that will have the worst (current) ratio
        for tile_candidate in tile_list:
            templated_tile = templated_tiles[tile_candidate.template]
            ratio = templated_tile['added'] / float(total_tiles)
            ratio /= templated_tile['ratio']
            if ratio < worst_ratio:
                worst_ratio = ratio
                tile = tile_candidate

        templated_tiles[tile.template]['added'] += 1

        return tile

    while len(result_tiles) < results + offset and len(result_tiles) < total_tiles:
        result_tiles.append(get_next_tile())

    print "Returning tiles: %s" % result_tiles[offset:]
    return qs_for(result_tiles[offset:])
