import argparse
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
    parser.add_argument('--file', help='Filename for export, otherwise, '
                                       'prints to stdout.')

    args, unknown = parser.parse_known_args();

    store_information = get_store_information(args.store)
    items = get_items(args.store)
    feed = generate_feed(store_information, items)

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

def get_items(store_id):
    response = ContentGraph.store(store_id).product.live.GET().json()
    items = response['results']

    # Get images
    for item in items:
        default_id = item.get('default-image-id')
        img_response = ContentGraph.store(store_id).content(default_id).GET().json()
        item['image'] = img_response['url']

    return items

def generate_feed(info, items):
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
        item_obj = json_to_XMLItem(item, info)
        channel.append(item_obj)

    return root

def json_to_XMLItem(obj, info=None):
    if not info:
        info = {}

    item = Element('item')

    # Begin - Always Required
    title = SubElement(item, 'title')
    title.text = obj.get('name')

    link = SubElement(item, 'link')
    link.text = obj.get('url')

    description = SubElement(item, 'description')
    description.text = obj.get('description')

    # Needs to be unique across everything!
    # Assumption: Product ids are unique across stores
    id = SubElement(item, 'g:id')
    id.text = '{0}{1}'.format(info.get('slug'), obj.get('id'))

    condition = SubElement(item, 'g:condition')
    condition.text = 'new'

    price = SubElement(item, 'g:price')
    price.text = obj.get('price')

    availability = SubElement(item, 'g:availability')
    availability.text = 'in stock'

    image_link = SubElement(item, 'g:image_link')
    image_link.text = obj.get('image')

    # End - Always Required

    # Begin - Required (Apparel)
    google_category = SubElement(item, 'g:google_product_category')
    google_category.text = 'Apparel &amp; Accessories &gt; Clothing'

    brand = SubElement(item, 'g:brand')
    brand.text = info.get('name')

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

    # Some sort of shipping / tax info is required
    # Hack: Lie about shipping weight
    shipping_weight = SubElement(item, 'g:shipping_weight')
    shipping_weight.text = '0 g'

    # Don't worry about variants for now.

    # End - Required (Apparel)

    return item

if __name__ == "__main__":
    sys.exit(main())