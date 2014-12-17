#!/usr/bin/env python

#argv - 1: page-id

import argparse
import urllib2
import hashlib
import xml.etree.ElementTree as etree

from time import gmtime, strftime, time
from xml.dom import minidom
from xml.etree.ElementTree import Element, tostring, SubElement
from apps.assets.models import Image, Page, Tile

DEFAULT_RESULTS = 35


def CDATA(text=None):
    element = etree.Element('![CDATA[')
    element.text = text
    return element


etree._original_serialize_xml = etree._serialize_xml


def _serialize_xml(write, elem, encoding, qnames, namespaces):
    if elem.tag == '![CDATA[':
        write("\n<%s%s]]>\n" % (
            elem.tag, elem.text))
        return
    return etree._original_serialize_xml(
        write, elem, encoding, qnames, namespaces)


etree._serialize_xml = etree._serialize['xml'] = _serialize_xml


def main(page, results=DEFAULT_RESULTS, google=False, feed_link=None, feed_name=None):
    """Returns an rss feed

    page -- the page model for the feed
    results -- the max number of results for the feed
    feed_name -- the name of the feed that is being created
    """
    store = page.store

    url = 'http://' + store.slug + '.secondfunnel.com/' + page.url_slug + '/'

    if not feed_link:
        feed_link = url + feed_name

    if google:
        feed = generate_google_feed(page, url, feed_link, results)
    else:
        feed = generate_feed(page, url, feed_link, results)

    return feed


def notify_superfeedr(url, feed_name='feed.rss'):
    url = 'http://second-funnel.superfeedr.com?hub.mode=publish&hub.url={0}'.format(url)
    r = urllib2.urlopen(url, data=' ')  # sending data to make this a post request


def tile_to_XML(url, tile, current_time):
    item = Element('item')

    products = tile.products.all()
    contents = tile.content.all()

    if len(contents) == 0:
        return None

    if len(products) > 0:
        product = products[0]
    else:
        product = None

    content = contents[0]

    image = Image.objects.get(content_ptr_id=content.id)

    title = SubElement(item, 'title')
    if product is not None:
        title.text = product.name
    elif image.name is not None:
        tile.text = image.name
    else:
        return None

    link = SubElement(item, 'link')
    link.text = url + '#' + str(tile.id)

    m = hashlib.md5()
    m.update(str(tile.id))
    guid = SubElement(item, 'guid')
    guid.set('isPermaLink', 'false')
    guid.set('id', str(tile.id))
    guid.text = m.hexdigest()

    pubDate = SubElement(item, 'pubDate')
    pubDate.text = strftime('%a, %d %b %Y %H:%M:%S +0000', gmtime(current_time))

    figure = Element('figure')

    img = SubElement(figure, 'img')
    if image.width and image.height:
        img.set('width', str(image.width))
        img.set('height', str(image.height))
    img.set('src', image.url)

    encoded = CDATA(tostring(figure, 'utf-8'))

    content_encoded = SubElement(item, 'content:encoded')
    content_encoded.append(encoded)

    return item


def generate_channel(page, url, feed_link, results=DEFAULT_RESULTS):
    channel = Element('channel')

    title = SubElement(channel, 'title')

    title.text = page.name

    link = SubElement(channel, 'link')
    link.text = url

    description = SubElement(channel, 'description')

    language = SubElement(channel, 'language')
    language.text = 'en-us'

    self_link = SubElement(channel, 'atom:link')
    self_link.set('rel', 'self')
    self_link.set('href', feed_link)
    self_link.set('xmlns', 'http://www.w3.org/2005/Atom')

    hub_link = SubElement(channel, 'atom:link')
    hub_link.set('rel', 'hub')
    hub_link.set('href', 'http://second-funnel.superfeedr.com/')
    hub_link.set('xmlns', 'http://www.w3.org/2005/Atom')

    current_time = time()
    cur_results = 0

    print page.feed_id

    for tile in Tile.objects.filter(feed_id=page.feed_id, template='image').order_by('-created_at').prefetch_related('products', 'content'):
        print tile.id
        item_obj = tile_to_XML(url, tile, current_time)
        if item_obj is not None:
            channel.append(item_obj)
            current_time -= 1
            cur_results += 1
        if cur_results >= results:
            break

    return channel


def generate_feed(page, url, feed_link, results=DEFAULT_RESULTS):
    root = Element('rss')
    root.set('version', '2.0')
    root.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')
    root.set('xmlns:dc', 'http://purl.org/dc/elements/1.1/')
    root.set('xmlns:media', 'http://search.yahoo.com/mrss/')
    root.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    root.set('xmlns:georss', 'http://www.georss.org/georss')

    channel = generate_channel(page, url, feed_link, results)

    root.append(channel)

    feed = tostring(root, 'utf-8')
    return minidom.parseString(feed).toprettyxml(indent='\t')


def generate_google_feed(page, url, feed_link, results=DEFAULT_RESULTS):
    root = Element('rss')
    root.set('version', '2.0')
    root.set('xmlns:g', 'http://base.google.com/ns/1.0')

    channel = SubElement(root, 'channel')

    page_title = SubElement(channel, 'title')
    page_title.text = page.name

    page_link = SubElement(channel, 'link')
    page_link.text = url

    page_description = SubElement(channel, 'description')
    page_description.text = page.description

    tiles = ir_base(feed=page.feed)

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
    pretty_feed = pretty_feed.replace('&quot;', '\"')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate a Flipboard RSS Feed.'
    )
    parser.add_argument('page_id', type=int, help='Page Identifier')

    args, unknown = parser.parse_known_args()

    page = Page.objects.get(id=args.page_id)

    print main(page)
