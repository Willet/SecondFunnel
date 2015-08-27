from itertools import chain

from django.conf import settings

from .utils import qs_for


def ir_priority(tiles, num_results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                offset=0, finite=False, *args, **kwargs):
    """
    Produce results based purely on priority.  Useful for homogenous feeds

    1. Tiles can be finite or infinite
    2. Any two tiles with an identical priority value can be ordered randomly
    3. Tiles will not be repeated until they are exhausted
    """
    # Make sure we do not have any duplicates
    ordered_tiles = tiles.order_by('-priority')

    num_tiles = ordered_tiles.count()
    if num_tiles == 0:
        return ordered_tiles

    if finite:
        # Finite feed, if offset > num_tiles will return empty Queryset
        return ordered_tiles[offset : offset + num_results]
    else:
        # Wrapping results
        overflow = num_results - num_tiles % num_results
        if num_results == overflow:
            overflow = 0

        # If offset greater then total tiles, figure out where it is looped back from start of tiles
        while offset >= num_tiles:
            offset -= overflow + num_tiles

        result_tiles = ordered_tiles[offset : offset + num_results]

        if len(result_tiles) < num_results:
            # Append missing tiles from start of feed
            result_tiles = qs_for(chain(result_tiles, ordered_tiles[:num_results - len(result_tiles)]))

        return result_tiles

