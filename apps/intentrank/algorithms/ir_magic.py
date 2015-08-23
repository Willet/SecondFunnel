from operator import itemgetter
from itertools import islice

from django.conf import settings

from .ir_priority import ir_priority
from .utils import qs_for


def ir_magic(tiles, num_results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
             offset=0, finite=False, *args, **kwargs):
    """
    For mixed content & product feeds - guaranteed to create a good mix

    NOTE: SLOW! this generates all the offsetted tiles every single time.

    1. Tiles can be finite or infinite
    2. Any two tiles with an identical priority value can be ordered randomly
    4. product/content ratio must be customizable BUT if available products/contents 
       count is above or beyond an "reasonable" value, then do not obey product/content ratio
    5. In no situation will algorithm attempt to repeat its content until necessary
    """
    if kwargs.get('products_only'):
        return ir_priority(tiles, num_results=num_results, offset=offset, finite=finite, *args, **kwargs)

    # Make sure we do not have any duplicates
    all_tiles = tiles.distinct('id', 'priority')

    total_tiles = all_tiles.count()
    if total_tiles == 0:
        return all_tiles

    # This feed is finite and has returned all of the tiles
    if feed and feed.is_finite and offset >= total_tiles \
        and not (page and page.theme_settings.get('override_finite_feed', False)):
        return qs_for([])

    # Wrapping results
    overflow = num_results - total_tiles % num_results
    if num_results == overflow:
        overflow = 0

    while offset >= total_tiles:
        offset -= overflow + total_tiles

    # Get the tiles out of an iterator
    itiles = islice(TemplateRatioEqualizer(tiles=all_tiles), offset, offset + num_results)
    result_tiles = [tile for tile in itiles]

    print "Returning tiles: %s" % result_tiles
    return qs_for(result_tiles)


class TemplateRatioEqualizer(object):
    """
    Generator of tiles based on:
     - get the highest priority tile from each template list
     - keep the ones that have the same highest priority
     - order them by worst ratio of already added vs ideal ratio given what tiles exist
    """
    def __init__(self, tiles):
        # Organize the tiles by template
        template_types = tiles.distinct('template').values_list('template', flat=True)
        self.containers = {
            template: TileRatioContainer(
                num_total_tiles= tiles.count(),
                tiles= list(tiles.filter(template=template).order_by('-priority')) ) \
            for template in template_types
        }
        
        self.candidates = []
        self.highest_priority = None

    def __iter__(self):
        return self

    def next(self):
        if not self.candidates and not self._get_next_highest_priority_tiles():
            raise StopIteration
        else:
            tile = self.candidates.pop(0)['tile']
            self._replace_tile_of_template(tile.template)
            return tile
    
    def _get_next_highest_priority_tiles(self):
        if self.candidates:
            return self.candidates
        else:
            # Of the available templates, get one of each template with the highest priority
            for template, container in self.containers.iteritems():
                candidate = container.get_next_tile(min_priority=self.highest_priority)
                if candidate:
                    if not self.candidates or candidate['tile'].priority > self.highest_priority:
                        self.candidates = [ candidate ]
                        self.highest_priority = candidate['tile'].priority
                    elif candidate.priority == self.highest_priority:
                        self.candidates.append(candidate)
            # Order the tiles by which template has the worst ratio relative
            # to other tile templates in the feed
            self.candidates.sort(key=itemgetter('ratio'))
            return self.candidates

    def _replace_tile_of_template(self, template):
        candidate = self.containers[template].get_next_tile()
        if candidate:
            self.candidates.append(candidate)
            self.candidates.sort(key=itemgetter('ratio')) # Fix!


class TileRatioContainer(object):
    """
    Holds a group of tiles in order and tracks the ratio of outputted
    tiles to the idealized ratio of all tiles
    """
    def __init__(self, tiles, num_total_tiles):
        self.tiles = tiles
        self.total = len(tiles)
        self.ratio = len(tiles) / float(num_total_tiles)
        self.num_total_tiles = num_total_tiles
        self.num_added = 0

    def get_next_tile(self, min_priority=None):
        if self.num_added == self.total:
            return None
        tile = self.tiles[self.num_added]
        ratio = (self.num_added / self.num_total_tiles) / self.ratio
        if isinstance(min_priority, int) and min_priority > tile.priority:
            return None
        else:
            self.num_added += 1
            return { 'tile': tile, 'ratio': ratio }

