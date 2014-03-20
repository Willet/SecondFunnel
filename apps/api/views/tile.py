import collections
from django.shortcuts import get_object_or_404
from apps.api.paginator import BaseItemCGHandler, BaseCGHandler
from apps.assets.models import Tile, Page


class TileItemCGHandler(BaseItemCGHandler):
    """Handler for managing tiles."""
    model = Tile
    id_attr = 'tile_id'  # the arg in the url pattern used to select something

    def serialize(self, things=None):
        return self.serialize_one(thing=things)

    def serialize_one(self, thing=None):
        """Converts the current object (or object list) to CG's JSON output."""
        if not thing:
            thing = self.object_list

        return thing.to_cg_json()


class TileCGHandler(BaseCGHandler):
    """Handler for managing tiles."""
    model = Tile
    id_attr = 'tile_id'  # the arg in the url pattern used to select something

    def serialize(self, things=None):
        """Converts the current object (or object list) to CG's JSON output."""
        if not things:
            things = self.object_list

        # multiple objects (paginate)
        if isinstance(things, collections.Iterable) and type(things) != dict:
            paginator, page, queryset, is_paginated = self.paginate_queryset(
                things, self.get_paginate_by(things))

            result_set = [obj.to_cg_json() for obj in page.object_list]
            if page.has_next():
                return {
                    'results': result_set,
                    'meta': {
                        'cursor': {
                            'next': page.next_page_number(),
                        },
                    },
                }
            else:
                return {
                    'results': result_set,
                }
        # single object
        return things.to_cg_json()


class PageTileCGHandler(TileCGHandler):
    """Adds filtering by page"""
    page = None

    def dispatch(self, *args, **kwargs):
        request = args[0]
        page_id = kwargs.get('page_id')
        self.page = get_object_or_404(Page, old_id=page_id)

        return super(PageTileCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        qs = super(PageTileCGHandler, self).get_queryset()
        return qs.filter(feed=self.page.feed)


class PageTileItemCGHandler(TileItemCGHandler):
    """Adds filtering by page"""
    page = None

    def dispatch(self, *args, **kwargs):
        request = args[0]
        page_id = kwargs.get('page_id')
        self.page = get_object_or_404(Page, old_id=page_id)

        return super(PageTileItemCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        qs = super(PageTileItemCGHandler, self).get_queryset()
        return qs.filter(feed=self.page.feed)


class StorePageTileCGHandler(PageTileCGHandler):
    """While semantically different, same as PageTileCGHandler in a
    relational DB"""
    pass


class StorePageTileItemCGHandler(PageTileItemCGHandler):
    """While semantically different, same as PageTileItemCGHandler in a
    relational DB"""
    pass
