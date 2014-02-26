#!/usr/bin/env python

#argv - 1: store-id, 2: page-id

import argparse
import urllib2
import hashlib

from time import gmtime, strftime, time
from apps.assets.models import Image, Page, Tile


def main(page, results=35, feed_name='feed.rss'):
    store = page.store

    url = 'http://' + store.slug + '.secondfunnel.com/' + page.url_slug + '/'

    feed = ''
    for line in generate_feed(page, url, results, feed_name):
        feed += line

    return feed


def notify_superfeedr(bucket, folder, feed_name='feed.rss'):
    url = 'http://second-funnel.superfeedr.com?hub.mode=publish&hub.url=http://' + bucket + '/' + folder + feed_name
    r = urllib2.urlopen(url, data=' ') # sending data to make this a post request


def tile_to_XML(url, tile, current_time):
    product = tile.products.first()
    content = tile.content.first()

    image = Image.objects.filter(content_ptr_id=content.id).first()

    yield '<title>' + product.name + '</title>\n'
    yield '<link>' + url + '#' + str(tile.old_id) + '</link>\n'

    m = hashlib.md5()
    m.update(str(tile.id))

    yield '<guid isPermaLink="false">' + m.hexdigest() + '</guid>\n'
    yield '<pubDate>' + strftime('%a, %d %b %Y %H:%M:%S +0000', gmtime(current_time)) + '</pubDate>\n'
    yield '<content:encoded><![CDATA[\n'
    yield '\t<figure>\n'
    img = '\t\t<img src="' + image.url.replace('master', '1024x1024')
    if image.width and image.height:
        img += ' width=' + str(image.width) + ' height=' + str(image.height)
    img += ' data-fl-original-src' + image.url + '">\n'
    yield img
    yield '\t</figure>\n'
    yield ']]></content:encoded>\n'


def generate_channel(page, url, results=35, feed_name='feed.rss'):

    yield '<title>' + page.name + '</title>\n'
    yield '<link>' + url + '</link>\n'
    yield '<description></description>\n'
    yield '<language>en-us</language>\n'
    yield '<atom:link rel="self" href="' + url + feed_name + '" xmlns="http://www.w3.org/2005/Atom"/>\n'
    yield '<atom:link rel="hub" href="http://second-funnel.superfeedr.com/" xmlns="http://www.w3.org/2005/Atom"/>\n'

    current_time = time()

    for tile in Tile.objects.filter(feed_id=page.feed_id, template='image')[0:results]:
        yield '<item>\n'
        for tile_line in tile_to_XML(url, tile, current_time):
            yield '\t' + tile_line
        current_time -= 1
        yield '</item>\n'


def generate_feed(page, url, results=35, feed_name='feed.rss'):
    yield '<rss version="2.0"\n'
    yield '\t xmlns:content="http://purl.org/rss/1.0/modules/content/"\n'
    yield '\t xmlns:dc="http://purl.org/dc/elements/1.1/"\n'
    yield '\t xmlns:media="http://search.yahoo.com/mrss/"\n'
    yield '\t xmlns:atom="http://www.w3.org/2005/Atom"\n'
    yield '\t xmlns:georss="http://www.georss.org/georss">\n'

    yield '\t<channel>\n'
    for channel_line in generate_channel(page, url, results, feed_name):
        yield '\t\t' + channel_line
    yield '\t</channel>\n'
    yield '</rss>'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate a Flipboard RSS Feed.'
    )
    parser.add_argument('page_id', type=int, help='Page Identifier')

    args, unknown = parser.parse_known_args()

    page = Page.objects.get(id=args.page_id)

    print main(page, args.bucket, args.folder)