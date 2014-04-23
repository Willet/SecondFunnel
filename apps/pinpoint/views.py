from itertools import ifilter
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring
from django.conf import settings
from apps.intentrank.algorithms import ir_base
from apps.intentrank.filters import in_stock

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError
from django.http.response import HttpResponseNotFound
from django.shortcuts import redirect, get_object_or_404, render_to_response
from django.template import Context, loader
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.vary import vary_on_headers

from apps.assets.models import Page, Tile, Store
from apps.pinpoint.utils import render_campaign, get_store_from_request, read_a_file


@login_required
def social_auth_redirect(request):
    """
    Redirect after some social-auth action (association, or disconnection).

    @param request: The request for this page.

    @return: An HttpResponse that redirects the user to the asset_manager
    page, or a page where the user can pick which store they want to view
    """
    store_set = request.user.store_set
    if store_set.count() == 1:
        return redirect('asset-manager', store_id=str(store_set.all()[0].id))
    else:
        return redirect('admin')


@cache_page(60 * 1, key_prefix="pinpoint-")  # a minute
@vary_on_headers('Accept-Encoding')
def campaign(request, store_id, page_id, mode=None):
    """Returns a rendered campaign response of the given id.

    :param mode   e.g. 'mobile' for the mobile page. Currently not functional.
    """
    rendered_content = render_campaign(page_id=page_id, request=request,
                                       store_id=store_id)

    return HttpResponse(rendered_content)


def campaign_by_slug(request, page_slug):
    """Used to render a page using only its name.

    If two pages have the same name (which was possible in CG), then django
    decides which page to render.
    """
    page_kwargs = {
        'url_slug': page_slug
    }

    store = get_store_from_request(request)

    if store:
        page_kwargs['store'] = store

    try:
        page = Page.objects.get(**page_kwargs)
    except Page.DoesNotExist:
        return HttpResponseNotFound()

    store_id = page.store.id
    return campaign(request, store_id=store_id, page_id=page.id)

# TODO: THis could probably just be a serializer on the Page object...
@never_cache
def product_feed(request, page_slug):
    page = get_object_or_404(Page, url_slug=page_slug)
    
    url = 'http://{}.secondfunnel.com/{}'.format(
        page.store.slug, page_slug
    )

    root = Element('rss')
    root.set('xmlns:g', 'http://base.google.com/ns/1.0')
    root.set('version', '2.0')

    channel = SubElement(root, 'channel')

    page_title = SubElement(channel, 'title')
    page_title.text = page.name

    page_link = SubElement(channel, 'link')
    page_link.text = url

    page_description = SubElement(channel, 'description')
    page_description.text = page.description

    tiles = ir_base(page.feed)

    # HACK: Voyage Prive MUST ONLY show in stock tiles.
    if page_slug == 'week-end':
        tiles = [x for x in tiles.all() if in_stock(x)]

    for obj in tiles:
        tile = obj.to_json()
        item = Element('item')

        tagged_products = tile.get('tagged-products', [])
        if len(tagged_products) > 0:
            product = tagged_products[0]
        else:
            product = tile

        # Begin - Always Required
        title = SubElement(item, 'title')
        title.text = product.get('name')

        # Since we can't link to gap.com and have the feed validate, need to
        # build the URL.

        # So, this is only really a solution in the short term.
        link = SubElement(item, 'link')

        if tile.get('template') == 'banner' and tile.get('redirect-url'):
            link.text = tile.get('redirect-url')
        else:
            link.text = '{}#{}'.format(
                 url,
                 tile.get('tile-id')
            )

        description = SubElement(item, 'description')
        description.text = product.get('description')

        # Needs to be unique across everything!
        # Assumption: Product ids are unique across stores
        id = SubElement(item, 'g:id')
        id.text = '{0}P{1}T{2}'.format(
            page.store.slug,
            page.id,
            tile.get('tile-id')
        )

        condition = SubElement(item, 'g:condition')
        condition.text = 'new'

        price = SubElement(item, 'g:price')
        price.text = product.get('sale_price') or product.get('price')

        availability = SubElement(item, 'g:availability')
        availability.text = 'in stock'

        image_id = int(product.get('default-image', 0))
        images = product.get('images', [])
        image = next(ifilter(lambda x: x.get('id') == image_id, images), {})

        if tile.get('facebook-ad'):
            image = tile.get('facebook-ad')

        image_link = SubElement(item, 'g:image_link')
        image_link.text = image.get('url')
        # End - Always Required

        # Begin - Required (Apparel)
        google_category = SubElement(item, 'g:google_product_category')
        google_category.text = 'Apparel &amp; Accessories &gt; Clothing'

        brand = SubElement(item, 'g:brand')
        brand.text = page.store.name

        # Our own categories
        product_type = SubElement(item, 'g:product_type')
        product_type.text = 'Uncategorized'

        # Hack: Force the product gender until we have it
        gender = SubElement(item, 'g:gender')
        gender.text = 'unisex'

        # Hack: Force the product age group until we have it
        age_group = SubElement(item, 'g:age_group')
        age_group.text = 'adult'

        # Hack: Force the product color until we have it
        color = SubElement(item, 'g:color')
        color.text = 'white'

        # Hack: Force the product size until we have it
        size = SubElement(item, 'g:size')
        size.text = 'M'

        # Shipping / Tax is required for US orders, see
        # https://support.google.com/merchants/answer/160162?hl=en&ref_topic=3404778

        # Don't worry about variants for now.

        # End - Required (Apparel)

        channel.append(item)

    feed = tostring(root, 'utf-8')
    pretty_feed = minidom.parseString(feed).toprettyxml(
        indent='\t', encoding='utf-8'
    )

    # TODO: Remove this code after the livedin campaign is finished
    # This code is being included so that past visitors may still be retargeted
    if page_slug == 'livedin':
        old_feed = read_a_file(
            'apps/pinpoint/static/pinpoint/legacy/lived_in.xml'
        )
        start_item = '<item>\n'
        end_item = '</item>\n'

        items = old_feed[
            old_feed.find(start_item):
            old_feed.rfind(end_item)+len(end_item)
        ]

        revised_feed = ''
        for line in pretty_feed.split('\n'):
            if '</channel>' in line:
                revised_feed += items
            revised_feed += line + '\n'

        pretty_feed = revised_feed

    return HttpResponse(
        pretty_feed, content_type='application/rss+xml; charset=utf-8'
    )

@login_required
def page_stats(request, page_slug):
    page = get_object_or_404(Page, url_slug=page_slug)
    return render_to_response('pinpoint/campaign_statistics.html', {
        'page': page,
        'keen': settings.KEEN_CONFIG
    })

def generate_static_campaign(request, store_id, page_id):
    """Too much confusion over the endpoint. Create alias for

    /pinpoint/id/id/regenerate == /static_pages/id/id/regenerate
    """
    from apps.static_pages.views import generate_static_campaign as real_gsc
    return real_gsc(request=request, store_id=store_id, page_id=page_id)


def app_exception_handler(request):
    """Renders the "something broke" page. JS console shows the error."""
    import sys, traceback

    _, exception, _ = sys.exc_info()
    stack = traceback.format_exc().splitlines()

    return HttpResponseServerError(loader.get_template('500.html').render(
        Context({'exception': exception,
                 'traceback': '\n'.join(stack)})))
