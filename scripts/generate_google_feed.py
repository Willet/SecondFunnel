import argparse
import json
import sys

from xml.dom import minidom
from xml.etree.ElementTree import Element, tostring, SubElement, ElementTree
from hammock import Hammock

ContentGraph = Hammock(
    'http://contentgraph-test.elasticbeanstalk.com/graph',
    headers={'ApiKey': 'secretword'}
)

# Don't know how to add this programmatically
FEED_HEADER = '<?xml version="1.0"?>'

def main():
    parser = argparse.ArgumentParser(
        description='Generate a Google Product Feed (RSS).'
    )
    parser.add_argument('store', type=int, help='Store Identifier')
    parser.add_argument('page', type=int, help='Page Identifier')
    parser.add_argument(
        '--file',
        help='Filename for export, otherwise, prints to stdout.'
    )
    parser.add_argument(
        '--url', required=True,
        help='Base URL for the page; should be possible to reach out to '
             'the content graph, but page information isn\'t actually part of'
             ' the content graph.'
    )

    args, unknown = parser.parse_known_args()

    store_information = get_store_information(args.store)
    page_information = get_page_information(args.page, args.url)
    items = get_items(args.page)
    feed = generate_feed(items, store_information, page_information)

    if args.file:
        save_feed(feed, args.file)
    else:
        print_feed(feed)


def save_feed(xml, filename):
    doc = ElementTree(xml)
    doc.write(filename)

def print_feed(xml):
    feed = tostring(xml, 'utf-8')
    pretty_feed = minidom.parseString(feed).toprettyxml(indent='\t')
    print pretty_feed

def get_store_information(store_id):
    information = ContentGraph.store(store_id).GET().json()
    return information

def get_page_information(page_id, url):
    return {'url': url}

def get_items(page_id):
    response = ContentGraph.page(page_id).tile.GET().json()
    items = response['results']

    items = map(tile_to_json, items)

    # Get images
    # for item in items:
    #     default_id = item.get('default-image-id')
    #     img_response = ContentGraph.store(store_id).content(default_id).GET().json()
    #     item['image'] = img_response['url']

    return items

def tile_to_json(tile_json):
    json_obj = json.loads(tile_json.get('json'))
    json_obj['page-id'] = tile_json.get('page-id')
    return json_obj

def generate_feed(items, store_info, page_info):
    root = Element('rss')
    root.set('xmlns:g', 'http://base.google.com/ns/1.0')
    root.set('version', '2.0')

    channel = SubElement(root, 'channel')

    title = SubElement(channel, 'title')
    title.text = 'Feed Title'

    link = SubElement(channel, 'title')
    link.text = 'http://www.secondfunnel.com'

    description = SubElement(channel, 'title')
    description.text = 'Feed description'

    for item in items:
        item_obj = json_to_XMLItem(item, store_info, page_info)
        channel.append(item_obj)

    return root

def json_to_XMLItem(tile, store_info=None, page_info=None):
    if not store_info:
        store_info = {}

    if not page_info:
        page_info = {}

    if len(tile.get('related-products', [])) > 0:
        product = tile.get('related-products')[0]
    else:
        product = tile

    item = Element('item')

    # Begin - Always Required
    title = SubElement(item, 'title')
    title.text = product.get('name')

    # Since we can't link to gap.com and have the feed validate, need to
    # build the URL.

    # So, this is only really a solution in the short term.
    link = SubElement(item, 'link')
    link.text = '{0}#{1}'.format(
        page_info.get('url'),
        tile.get('tile-id')
    )

    description = SubElement(item, 'description')
    description.text = product.get('description')

    # Needs to be unique across everything!
    # Assumption: Product ids are unique across stores
    id = SubElement(item, 'g:id')
    id.text = '{0}P{1}T{2}'.format(
        store_info.get('slug'),
        tile.get('page-id'),
        tile.get('tile-id')
    )

    condition = SubElement(item, 'g:condition')
    condition.text = 'new'

    price = SubElement(item, 'g:price')
    price.text = product.get('price')

    availability = SubElement(item, 'g:availability')
    availability.text = 'in stock'

    image_link = SubElement(item, 'g:image_link')

    if tile is product:
        image_link.text = product.get('images')[0]['url']
    else:
        image_link.text = tile.get('url')

    # End - Always Required

    # Begin - Required (Apparel)
    google_category = SubElement(item, 'g:google_product_category')
    google_category.text = 'Apparel &amp; Accessories &gt; Clothing'

    brand = SubElement(item, 'g:brand')
    brand.text = store_info.get('name')

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

    return item

if __name__ == "__main__":
    sys.exit(main())