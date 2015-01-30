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
    
    #
    # If the page has a state, look it up
    #
    tile = None
    category = None

    # /summersales/tile/123 or /fallishere/preview/456
    if identifier in ['tile', 'preview']:
        tiles = Tile.objects.filter(id=identifier_value)
        if len(tiles):
            tile = tiles[0]

    # /livedin/id/789 or /dressnormal/sku/012
    elif identifier in ['id', 'sku']:
        try:
            # NOTE: I'm not sure why this more complicated query is required
            # leaving it commented in case we run into problems and need it
            # if a store has two or more products with the same sku,
            # assume the one the user wanted is the one with
            # - the most tiles
            # - has at least a tile
            #lookup_map = {
            #   identifier: identifier_value,
            #   'store': store,
            #}
            #product = (Product.objects.filter(**lookup_map)
            #                  .annotate(num_tiles=Count('tiles'))
            #                  .filter(num_tiles__gt=0)
            #                  .order_by('-num_tiles')[0])
            product = None
            lookup_map = {
                identifier: identifier_value,
            }
            product = Product.objects.get(**lookup_map)
            if not product:
                tile = None
            else:
                tile = product.tiles.all()[0]
        except (Product.DoesNotExist, IndexError, ValueError):
            tile = None

    elif identifier in ['category']:
        category = identifier_value

    tests = page.get('test')

    algorithm = request.GET.get('algorithm', page.feed.feed_algorithm or 'magic')

    #
    # Build rendering context
    #

    render_context = {}
    render_context['store'] = store
    render_context['test'] = tests
    render_context['algorithm'] = algorithm
    render_context['ir_base_url'] = '/intentrank'
    render_context['tile'] = tile.to_json() if tile else {}
    render_context['hero'] = tile['tile-id'] if (identifier == 'tile') else None
    render_context['preview'] = tile['tile-id'] if (identifier == 'preview') else None
    render_context['category'] = category

    return HttpResponse(render_landing_page(request, page, render_context))


def render_landing_page(request, page, render_context):
    """
    :returns {str|unicode}
    """
    store = page.store
    tile = render_context.get('tile', None)
    initial_state = {
        'category': render_context.get('category', None),
        'hero': render_context.get('hero', None),
        'preview': render_context.get('preview', None),
    }

    tests = []
    if page.get('tests'):
        tests = json.dumps(page.get('tests'))
    if page.get('wideable_templates'):
        page.wideable_templates = json.dumps(page.get('wideable_templates'))

    algorithm = get_algorithm(request=request, page=page)
    PAGES_INFO = PageConfigSerializer.to_json(request=request, page=page,
        feed=page.feed, store=store, algorithm=algorithm, init=initial_state,
        other={'tile_set': ''})
    
    initial_results = []  # JS now fetches its own initial results

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
