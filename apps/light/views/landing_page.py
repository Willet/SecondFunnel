import json
from datetime import datetime
import random

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext, loader
from django.views.decorators.cache import cache_page, cache_control
from django.views.decorators.vary import vary_on_headers

from apps.assets.models import Page, Store, Product, Tile
from apps.intentrank.serializers import PageConfigSerializer
from apps.light.utils import get_store_from_request, get_algorithm


@cache_control(must_revalidate=True, max_age=(1 * 60))
@cache_page(60 * 1, key_prefix="landingpage-")  # a minute
@vary_on_headers('Accept-Encoding')
def landing_page(request, page_slug, identifier='id', identifier_value=''):
    """Used to render a page using only its name.

    If two pages have the same name (which was possible in CG), then django
    decides which page to render.

    :param identifier: selects the featured product.
           allowed values: 'id', 'sku', or 'tile' (whitelisted to prevent abuse)
    :param identifier_value: the product or tile's id or sku, respectively
    """
    #
    # Verify a page exists with the page slug
    # and the domain it was accessed on
    #

    # get the subdomain which should equal the store's slug
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
    if page.dashboard_settings.get('redirect_to', False):
        return HttpResponseRedirect(page.dashboard_settings.get('redirect_to'))
    
    #
    # Lookup Product for Shop-The-Look style pages
    #

    product = None
    product_id = request.GET.get('product_id', None)
    product_sku = request.GET.get('product_sku', None)
    if product_id:
        product = Product.objects.get(product_id)
    elif product_sku:
        product = Product.objects.get(sku=product_sku)

    tile = None
    tile_id = request.GET.get('tile_id', None)
    if tile_id:
        tile = Tile.objects.get(tile_id)
    elif product:
        tile = Tile.objects.filter(feed__id=page.feed_id, products__id=product.id).order_by('-template')[0]

    # if necessary, get tile
    # livedin/sku/123
    lookup_map = {identifier: identifier_value}
    if request.GET.get('product_id'):  # livedin?product_id=123
        lookup_map = {'id': request.GET.get('product_id')}
    lookup_map['store'] = store

    if not tile and identifier in ['id', 'sku']:
        try:
            # if a store has two or more products with the same sku,
            # assume the one the user wanted is the one with
            # - the most tiles
            # - has at least a tile
            product = (Product.objects.filter(**lookup_map)
                              .annotate(num_tiles=Count('tiles'))
                              .filter(num_tiles__gt=0)
                              .order_by('-num_tiles')[0])
            if not product:
                tile = None
            else:
                tile = product.tiles.all()[0]
        except (Product.DoesNotExist, IndexError, ValueError):
            tile = None
    elif not tile and identifier == 'tile':
        tiles = Tile.objects.filter(id=identifier_value)
        if len(tiles):
            tile = tiles[0]

    tests = page.get('test')

    algorithm = request.GET.get('algorithm', page.feed.feed_algorithm or 'generic')
    if request.GET.get('popular', None) == '':  # handle ?popular
        algorithm = 'popular'

    #
    # Build rendering context
    #

    render_context = {}
    render_context['store'] = store
    render_context['product'] = product
    render_context['test'] = tests
    render_context['algorithm'] = algorithm
    render_context['ir_base_url'] = '/intentrank'

    if tile:
        render_context['tile'] = tile.to_json()
    else:
        render_context['tile'] = None

    return HttpResponse(render_landing_page(request, page, render_context))


def render_landing_page(request, page, render_context):
    """
    :returns {str|unicode}
    """
    store = page.store
    tile = render_context.get('tile', None)

    tests = []
    if page.get('tests'):
        tests = json.dumps(page.get('tests'))
    if page.get('wideable_templates'):
        page.wideable_templates = json.dumps(page.get('wideable_templates'))

    algorithm = get_algorithm(request=request, page=page)
    PAGES_INFO = PageConfigSerializer.to_json(request=request, page=page,
        feed=page.feed, store=store, algorithm=algorithm, featured_tile=tile,
        other={'tile_set': ''})

    initial_results = []  # JS now fetches its own initial results

    # TODO: structure this
    #       and escape: simplejson.dumps(s1, cls=simplejson.encoder.JSONEncoderForHTML)
    attributes = {
        "algorithm": algorithm or 'magic',
        "campaign": page or 'undefined',
        "columns": range(4),
        "column_width": page.column_width or store.get('column-width', ''),
        "desktop_hero_image": page.desktop_hero_image,
        "enable_tracking": page.enable_tracking,  # jsbool
        "environment": settings.ENVIRONMENT,
        "ga_account_number": settings.GOOGLE_ANALYTICS_PROPERTY,
        "image_tile_wide": page.image_tile_wide,
        "initial_results": initial_results,
        "keen_io": settings.KEEN_CONFIG,
        "legal_copy": page.legal_copy or '',
        "mobile_hero_image": page.mobile_hero_image,
        "open_tile_in_popup": "true" if page.get("open_tile_in_popup") else "false",
        "PAGES_INFO": PAGES_INFO,
        "preview": False,  # TODO: was this need to fix: not page.live,
        "pub_date": datetime.now().isoformat(),
        "session_id": request.session.session_key,
        "store": store,
        "tests": tests,
        "tile": tile,
        "url": page.get('url', ''),
        "url_params": json.dumps(page.get("url_params", {})),
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
