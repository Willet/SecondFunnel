from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template import RequestContext, loader
from django.views.decorators.cache import cache_page, cache_control
from django.views.decorators.vary import vary_on_headers

from apps.assets.models import Page, Store, Product, Tile


@cache_control(must_revalidate=True, max_age=(1 * 60))
@cache_page(60 * 1, key_prefix="landingpage-")  # a minute
@vary_on_headers('Accept-Encoding')
def landing_page(request, page_slug):

    #
    # Verify a page exists with the page slug
    # and the domain it was accessed on
    #

    # get the subdomain which should equal the store's slug
    store_slug = request.get_host().split('.')[0]

    store = get_object_or_404(Store, slug=store_slug)
    page = get_object_or_404(Page, store=store, url_slug=page_slug)

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
    render_context['tile'] = tile
    render_context['test'] = tests
    render_context['algorithm'] = algorithm
    render_context['ir_base_url'] = '/intentrank'

    return HttpResponse(render_landing_page(request, page, render_context))


def render_landing_page(request, page, render_context):

    # TODO: structure this
    #       and escape: simplejson.dumps(s1, cls=simplejson.encoder.JSONEncoderForHTML)
    attributes = {
        "session_id": request.session.session_key,
        "campaign": page or 'undefined',
        "columns": range(4),
        "preview": False,  # TODO: was this need to fix: not page.live,
        "initial_results": [],  # JS now fetches its own initial results
        "backup_results": [],
        "social_buttons": page.social_buttons or page.store.get('social-buttons', ''),
        "conditional_social_buttons": page.get('conditional_social_buttons', {}),
        "enable_tracking": page.enable_tracking,  # jsbool
        # apparently {{ campaign.image_tile_wide|default:0.5 }} is too confusing for django
        "image_tile_wide": page.image_tile_wide,
        "pub_date": datetime.now().isoformat(),
        "legal_copy": page.legal_copy or '',
        "mobile_hero_image": page.mobile_hero_image,
        "desktop_hero_image": page.desktop_hero_image,
        "ga_account_number": settings.GOOGLE_ANALYTICS_PROPERTY,
        "keen_io": settings.KEEN_CONFIG,
        "url": page.get('url', ''),
        "environment": settings.ENVIRONMENT
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
