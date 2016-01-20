from functools import wraps
import logging

from django.db.models import Q
from django.db.models.query import QuerySet

from apps.assets.models import Tile


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

        if num_results < 1:  # nothing to get
            return qs_for([])

        # Note: every QuerySet call clones the QuerySet, so combine all
        # filters into a single query

        if tiles:
            if not isinstance(tiles, QuerySet):
                tiles = qs_for(tiles)
        elif not feed:
            raise ValueError("Either tiles or feed must be supplied")
        else:
            logging.debug(feed.tiles)
            tiles = feed.tiles
        
        # Filter out of stock tiles
        filters = Q(placeholder=False)

        logging.debug(feed.store.display_out_of_stock)

        if not feed.store.display_out_of_stock:
            filters = filters & Q(in_stock=True)

        if allowed_set:
            filters = filters & Q(id__in=allowed_set)
        if exclude_set:
            filters = filters & ~Q(id__in=exclude_set)
        
        # Banner tiles are special tiles meant to link elsewhere
        # Force them into all feeds
        if products_only:
            filters = filters & Q(template__in=['product','banner'])
        elif content_only:
            filters = filters & Q(template__in=['product','banner'])

        logging.debug(filters)

        tiles = tiles.filter(filters)

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
