import json
import sys
from xml.dom import minidom
from xml.etree.ElementTree import Element, tostring, SubElement
from hammock import Hammock

ContentGraph = Hammock(
    'http://contentgraph-test.elasticbeanstalk.com/graph',
    headers={'ApiKey': 'secretword'}
)

def main(argv=None):
    if argv is None:
        argv = sys.argv

    store_id = 38

    info = get_store_information(store_id)
    items = get_items(store_id)

    feed = generate_feed(info, items)
    ugly_feed = tostring(feed, 'utf-8')
    pretty_feed = minidom.parseString(ugly_feed).toprettyxml(indent='\t')
    print pretty_feed

def get_store_information(store_id):
    response = ContentGraph.store(store_id).GET()
    information = json.loads(response.content)
    return information

def get_items(store_id):
    response = ContentGraph.store(store_id).product.live.GET()
    json_response = json.loads(response.content)
    items = json_response['results']

    # Get images
    for item in items:
        default_id = item.get('default-image-id')
        img_response = ContentGraph.store(store_id).content(default_id).GET()
        item['image'] = json.loads(img_response.content)['url']

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
    description.text = ''

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
    link.text=obj.get('url')

    description = SubElement(item, 'description')
    description.text=obj.get('description')

    # Needs to be unique across everything!
    # Assumption: Product ids are unique across stores
    id = SubElement(item, 'g:id')
    id.text = '{0}{1}'.format(info.get('slug'), obj.get('id'))

    condition = SubElement(item, 'g:condition')
    condition.text='new'

    price = SubElement(item, 'g:price')
    price.text=obj.get('price')

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

    # TODO: How do we get this information?
    gender = SubElement(item, 'g:gender')
    gender.text = ''

    # TODO: How do we get this information?
    age_group = SubElement(item, 'g:age_group')
    age_group.text = ''

    # TODO: How do we get this information?
    color = SubElement(item, 'g:color')
    color.text = ''

    # TODO: How do we get this information?
    size = SubElement(item, 'g:size')
    size.text = ''

    # Some sort of shipping / tax info is required
    # Since we don't have this, we cheat
    shipping_weight = SubElement(item, 'g:shipping_weight')
    shipping_weight = '0 g'

    # Don't worry about variants for now.

    # End - Required (Apparel)

    return item

if __name__ == "__main__":
    sys.exit(main())