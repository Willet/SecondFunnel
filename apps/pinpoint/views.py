from itertools import ifilter
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring
from django.core.urlresolvers import reverse
from django.template.defaulttags import url

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError
from django.http.response import HttpResponseNotFound
from django.shortcuts import redirect, get_object_or_404
from django.template import Context, loader
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.vary import vary_on_headers

from apps.assets.models import Page, Tile
from apps.pinpoint.utils import render_campaign, get_store_from_request


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

    root = Element('rss')
    root.set('xmlns:g', 'http://base.google.com/ns/1.0')
    root.set('version', '2.0')

    channel = SubElement(root, 'channel')

    page_title = SubElement(channel, 'title')
    page_title.text = page.name

    page_link = SubElement(channel, 'link')
    page_link.text = request.build_absolute_uri()

    page_description = SubElement(channel, 'description')
    page_description.text = page.description

    for obj in page.feed.tiles.all():
        tile = obj.to_json()
        item = Element('item')

        # Begin - Always Required
        title = SubElement(item, 'title')
        title.text = tile.get('name')

        # Since we can't link to gap.com and have the feed validate, need to
        # build the URL.

        # So, this is only really a solution in the short term.
        link = SubElement(item, 'link')
        link.text = 'http://{}/{}#{}'.format(
             request.get_host(),
             page_slug,
             tile.get('tile-id')
        )

        description = SubElement(item, 'description')
        description.text = tile.get('description')

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
        price.text = tile.get('price')

        availability = SubElement(item, 'g:availability')
        availability.text = 'in stock'

        image_id = int(tile.get('default-image', 0))
        images = tile.get('images', [])
        image = next(ifilter(lambda x: x.get('id') == image_id, images), {})

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
    pretty_feed = minidom.parseString(feed).toprettyxml(indent='\t')

    return HttpResponse(pretty_feed, content_type='application/rss+xml')

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
