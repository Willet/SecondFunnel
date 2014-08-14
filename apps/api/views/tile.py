from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from apps.api.paginator import BaseItemCGHandler, BaseCGHandler
from apps.assets.models import Tile, Page


class TileItemCGHandler(BaseItemCGHandler):
    """Handler for managing tiles."""
    model = Tile
    id_attr = 'tile_id'  # the arg in the url pattern used to select something


class TileCGHandler(BaseCGHandler):
    """Handler for managing tiles."""
    model = Tile
    id_attr = 'tile_id'  # the arg in the url pattern used to select something


class PageTileCGHandler(TileCGHandler):
    """Adds filtering by page"""
    page = None

    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        page_id = kwargs.get('page_id')
        self.page = get_object_or_404(Page, id=page_id)

        return super(PageTileCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        qs = super(PageTileCGHandler, self).get_queryset()
        return qs.filter(feed=self.page.feed)


class PageTileItemCGHandler(TileItemCGHandler):
    """Adds filtering by page"""
    page = None

    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        page_id = kwargs.get('page_id')
        self.page = get_object_or_404(Page, id=page_id)

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
