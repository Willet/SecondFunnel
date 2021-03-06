import json
from datetime import datetime
from urlparse import urlparse
import random

from django.conf import settings
from django.core.validators import URLValidator
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext, loader
from django.views.decorators.cache import cache_page, cache_control
from django.views.decorators.vary import vary_on_headers
from django.utils.safestring import SafeString

from apps.assets.models import Page, Store, Product, Tile
from apps.intentrank.serializers import PageConfigSerializer
from apps.light.utils import get_store_from_request, get_algorithm
from apps.utils.classes import AttrDict


@cache_control(must_revalidate=True, max_age=(1 * 60))
@cache_page(60 * 1, key_prefix="landingpage-")  # a minute
@vary_on_headers('Accept-Encoding')
def landing_page(request, page_slug, identifier='', identifier_value=''):
    """Used to render a page using only its name.

    :param identifier:
        'id', 'sku' - a product that will be loaded into the hero area
        'tile' - a tile that will be loaded into the hero area
        'preview' - a tile that will be previewed
        'category' - category to load to
    :param identifier_value: the product or tile's id or sku, respectively
    """
    #
    # Verify a page exists with the page slug
    # and the domain it was accessed on
    #

    # get the subdomain which should equal the store's slug
    print "identifier=%s\nidentifier_value=%s" % (identifier, identifier_value)
    store_slug = request.get_host().split('.')[0]

    try:
        store = get_store_from_request(request)
    except (IndexError, ObjectDoesNotExist):
        store = None

    if store:
        page = get_object_or_404(Page, store=store, url_slug=page_slug)
    else:
        page = get_object_or_404(Page, url_slug=page_slug)
        store = page.store

    # Support for redirects for when a campaign is over
    if page.dashboard_settings.get('redirect_to'):
        url = page.dashboard_settings.get('redirect_to')
        validator = URLValidator()
        try:
            validator(url)
        except ValidationError:
            url = settings.WEBSITE_BASE_URL
        parts = urlparse(url)
        # missing netloc indicates no protocol was set
        if not parts.netloc:
            url = '//' + url
        return HttpResponseRedirect(url)
    
    # If the page has a state, look it up
    # Also, cache the initial state & a hero tile
    tile = category = None
    tiles = []
    tile_ids = []
    hero_tile = getattr(page, 'home', {}).get('hero', None)

    # /summersales/tile/123 or /fallishere/preview/456
    if identifier in ['tile', 'preview']:
        tile_ids.append(identifier_value)

    if hero_tile:
        tile_ids.append(hero_tile)

    if len(tile_ids):
        # get tiles for caching
        try:
            tiles = Tile.objects.filter(id__in=tile_ids)
            # tile is just the one specified in the url
            tile = next((tile for tile in tiles if tile.id == identifier_value), None)
        except ValueError:
            tile = None

    # /livedin/id/789 or /dressnormal/sku/012
    if identifier in ['id', 'sku']:
        try:
            product = None
            lookup_map = {
                identifier: identifier_value,
            }
            product = Product.objects.get(**lookup_map)
            tile = product.tiles.first() if product else None
        except (Product.DoesNotExist, ValueError):
            tile = None

    # /aeropostale/category/for-her
    elif identifier in ['category']:
        category = identifier_value

    algorithm = request.GET.get('algorithm', page.feed.feed_algorithm or 'magic')

    # Build rendering context
    render_context = {
        'store': store,
        'algorithm': algorithm,
        'ir_base_url': '/intentrank',
        'tile': (tile.to_json() if getattr(tile, 'to_json', False) else {}),
        'tiles': [ tile.to_json() for tile in tiles ],
        'hero': (getattr(tile, 'id', None) if (identifier == 'tile') else None),
        'preview': (getattr(tile, 'id', None) if (identifier == 'preview') else None),
        'category': category,
    }

    return HttpResponse(render_landing_page(request, page, render_context))


def render_landing_page(request, page, render_context):
    """
    :returns {str|unicode}
    """
    store = page.store
    tile = render_context.get('tile', None)
    initial_state = AttrDict({
        'category': render_context.get('category', None),
        'hero': render_context.get('hero', None),
        'preview': render_context.get('preview', None),
    })

    algorithm = get_algorithm(request=request, page=page)
    PAGES_INFO = PageConfigSerializer.to_json(request=request, page=page,
        feed=page.feed, store=store, algorithm=algorithm, init=initial_state,
        other={'tile_set': ''})
    
    initial_results = [] # JS now fetches its own initial results

    # TODO: structure this
    #       and escape: simplejson.dumps(s1, cls=simplejson.encoder.JSONEncoderForHTML)
    attributes = {
        "algorithm": algorithm or 'magic',
        "campaign": page or 'undefined',
        "columns": range(4),
        "column_width": page.column_width or store.get('column-width', ''),
        "enable_tracking": page.enable_tracking,  # jsbool
        "environment": settings.ENVIRONMENT,
        "ga_account_number": settings.GOOGLE_ANALYTICS_PROPERTY,
        "initial_results": initial_results,
        "keen_io": settings.KEEN_CONFIG,
        "PAGES_INFO": PAGES_INFO,
        "preview": False,  # TODO: was this need to fix: not page.live,
        "pub_date": datetime.now().isoformat(),
        "session_id": request.session.session_key,
        "store": store,
        "tiles": [ tile ] if tile else [],
    }

    attributes.update(render_context)

    # make all None undefined
    for key, val in attributes.items():
        if val is None:
            attributes[key] = 'undefined'

    context = RequestContext(request, attributes)

    # Page content
    template = loader.select_template(["light/%s" % page.theme.template])

    # Render response
    return template.render(context)
