import collections
from django.contrib.auth.decorators import login_required

from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.api.paginator import BaseItemCGHandler, BaseCGHandler
from apps.assets.models import Page, Tile


class TileConfigItemCGHandler(BaseItemCGHandler):
    """EMULATED handler for managing tiles."""
    model = Tile
    id_attr = 'tileconfig_id'  # the arg in the url pattern used to select something

    def serialize(self, things=None):
        return self.serialize_one(thing=things)

    def serialize_one(self, thing=None):
        """Converts the current object (or object list) to CG's JSON output."""
        if not thing:
            thing = self.object_list

        return thing.tile_config


class TileConfigCGHandler(BaseCGHandler):
    """EMULATED handler for managing tiles."""
    model = Tile
    id_attr = 'tileconfig_id'  # the arg in the url pattern used to select something

    def serialize(self, things=None):
        """Converts the current object (or object list) to CG's JSON output."""
        if not things:
            things = self.object_list

        # multiple objects (paginate)
        if isinstance(things, collections.Iterable) and type(things) != dict:
            paginator, page, queryset, is_paginated = self.paginate_queryset(
                things, self.get_paginate_by(things))

            result_set = [obj.tile_config for obj in page.object_list]
            if page.has_next():
                return {
                    'results': result_set,
                    'meta': {
                        'cursors': {
                            'next': page.next_page_number(),
                        },
                    },
                }
            else:
                return {
                    'results': result_set,
                }
        # single object
        return things.tile_config


class PageTileConfigCGHandler(TileConfigCGHandler):
    """Adds filtering by page"""
    page = None

    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        request = args[0]
        page_id = kwargs.get('page_id')
        self.page = get_object_or_404(Page, id=page_id)

        return super(PageTileConfigCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        qs = super(PageTileConfigCGHandler, self).get_queryset()
        return qs.filter(feed=self.page.feed)


class PageTileConfigItemCGHandler(TileConfigItemCGHandler):
    """Adds filtering by page"""
    page = None

    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        request = args[0]
        page_id = kwargs.get('page_id')
        self.page = get_object_or_404(Page, id=page_id)

        return super(PageTileConfigItemCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        qs = super(PageTileConfigItemCGHandler, self).get_queryset()
        return qs.filter(feed=self.page.feed)


class StorePageTileConfigCGHandler(PageTileConfigCGHandler):
    """While semantically different, same as PageTileConfigCGHandler in a
    relational DB"""
    pass


class StorePageTileConfigItemCGHandler(PageTileConfigItemCGHandler):
    """While semantically different, same as PageTileConfigItemCGHandler in a
    relational DB"""
    pass
