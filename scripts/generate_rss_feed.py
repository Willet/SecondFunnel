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

DEFAULT_RESULTS=35

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


def main(page, results=DEFAULT_RESULTS, feed_link=None, feed_name=None):
    """Returns an rss feed

    page -- the page model for the feed
    results -- the max number of results for the feed
    feed_name -- the name of the feed that is being created
    """
    store = page.store

    url = 'http://' + store.slug + '.secondfunnel.com/' + page.url_slug + '/'

    if not feed_link:
        feed_link = url + feed_name

    feed = generate_feed(page, url, feed_link, results)

    return feed


def notify_superfeedr(url, feed_name='feed.rss'):
    url = 'http://second-funnel.superfeedr.com?hub.mode=publish&hub.url={0}'.format(url)
    r = urllib2.urlopen(url, data=' ') # sending data to make this a post request


def tile_to_XML(url, tile, current_time):
    item = Element('item')

    product = tile.products.first()
    content = tile.content.first()

    image = Image.objects.filter(content_ptr_id=content.id).first()

    title = SubElement(item, 'title')
    title.text = product.name

    link = SubElement(item, 'link')
    link.text = url + '#' + str(tile.old_id)

    m = hashlib.md5()
    m.update(str(tile.id))
    guid = SubElement(item, 'guid')
    guid.set('isPermaLink', 'false')
    guid.text = m.hexdigest()

    pubDate = SubElement(item, 'pubDate')
    pubDate.text = strftime('%a, %d %b %Y %H:%M:%S +0000', gmtime(current_time))

    figure = Element('figure')

    img = SubElement(figure, 'img')
    img.set('src', image.url.replace('master', '1024x1024'))
    if image.width and image.height:
        img.set('width', str(image.width))
        img.set('height', str(image.height))
    img.set('data-fl-original-src', image.url)

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

    for tile in Tile.objects.filter(feed_id=page.feed_id, template='image')[0:results]:
        item_obj = tile_to_XML(url, tile, current_time)
        channel.append(item_obj)
        current_time -= 1

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate a Flipboard RSS Feed.'
    )
    parser.add_argument('page_id', type=int, help='Page Identifier')

    args, unknown = parser.parse_known_args()

    page = Page.objects.get(id=args.page_id)

    print main(page)
    