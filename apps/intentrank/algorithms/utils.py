from functools import wraps

from django.db.models.query import QuerySet

from apps.assets.models import Tile


def filter_excluded(tiles, allowed_set=None, exclude_set=None):
    """Given a Tile QuerySet, apply allowed_set and/or exclude_set to it
    if present.
    """
    if allowed_set:
        tiles = tiles.filter(id__in=allowed_set)
    if exclude_set:
        tiles = tiles.exclude(id__in=exclude_set)
    return tiles

def filter_tiles(fn):
    """Algorithm with this decorator receives a list of tiles that already
    have allowed_set and exclude_sets filtered.

    The algorithm will also be forced to return a QuerySet.
    """

    @wraps(fn)
    def wrapped_fn(*args, **kwargs):
        tiles = kwargs.get('tiles')
        feed = kwargs.get('feed')
        allowed_set = kwargs.get('allowed_set', None)
        exclude_set = kwargs.get('exclude_set', None)
        num_results = kwargs.get('num_results', 10)
        content_only = kwargs.get('content_only', False)
        products_only = kwargs.get('products_only', False)

        if not feed and tiles is None:  # permit [] for tiles
            raise ValueError("Either tiles or feed must be supplied")

        if tiles is None and feed:
            tiles = feed.tiles.all()
        if not tiles:  # nothing to give
            return qs_for([])

        if num_results < 1:  # nothing to get
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

        # Filter out of stock tiles
        # TODO: move out of stock to tile model
        tiles = tiles.exclude(products__in_stock=False)\
                     .exclude(content__tagged_products__in_stock=False)

        kwargs.update({
            'tiles': tiles,
        })
        tiles = fn(*args, **kwargs)

        if not isinstance(tiles, QuerySet):
            tiles = qs_for(tiles)

        return tiles

    return wrapped_fn

def qs_for(tiles):
    """Convert a list of tiles to a queryset containing those tiles.

    Executes at least one query.

    :returns {QuerySet}
    """
    if isinstance(tiles, QuerySet):
        return tiles

    elif not tiles:
        return Tile.objects.none()

    else:
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
