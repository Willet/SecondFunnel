#!/usr/bin/env python

#argv - 1: store-id, 2: page-id

import argparse
import time
import urllib2
import hashlib
import apps.static_pages.aws_utils as aws_utils

from time import gmtime, strftime
from apps.assets.models import Store, Image, Page, Tile

RESULTS = 35

FEED_NAME = 'feed.rss'


def main():
    parser = argparse.ArgumentParser(
        description='Generate a Flipboard RSS Feed.'
    )
    parser.add_argument('store_id', type=int, help='Store Identifier')
    parser.add_argument('page_id', type=int, help='Page Identifier')
    parser.add_argument('bucket', help='Page bucket')
    parser.add_argument('folder', help='Page folder')

    args, unknown = parser.parse_known_args()

    url = 'http://' + args.bucket + '/' + args.folder

    feed = ''
    for line in generate_feed(args.store_id, args.page_id, url):
        feed += line

    upload_feed(feed, args.bucket, args.folder)

    notify_superfeedr(args.bucket, args.folder)


def notify_superfeedr(bucket, folder):
    url = 'http://second-funnel.superfeedr.com?hub.mode=publish&hub.url=http://' + bucket + '/' + folder + FEED_NAME
    r = urllib2.urlopen(url, data=' ') # sending data to make this a post request


def upload_feed(xml, bucket, folder):
    aws_utils.upload_to_bucket(bucket, folder + FEED_NAME, xml, content_type='application/rss+xml', public=True, do_gzip=False)


def tile_to_XML(url, tile):
    product = tile.products.first()
    content = tile.content.first()

    image = Image.objects.filter(content_ptr_id=content.id).first()

    yield '<title>' + product.name + '</title>\n'
    url_parts = url.split('/')
    campaign = url_parts[-1] or url_parts[-2]
    yield '<link>' + url + '?utm_source=flipboard&utm_medium=rss-feed&utm_campaign=' + campaign + '#' + str(tile.old_id) + '</link>\n'

    m = hashlib.md5()
    m.update(str(tile.id))

    yield '<guid isPermaLink="false">' + m.hexdigest() + '</guid>\n'
    yield '<pubDate>' + strftime('%a, %d %b %Y %H:%M:%S +0000', gmtime()) + '</pubDate>\n'
    yield '<content:encoded><![CDATA[\n'
    yield '\t<figure>\n'
    img =  '\t\t<img src="' + image.url.replace('master', '1024x1024')
    if image.width and image.height:
        img += ' width=' + str(image.width) + ' height=' + str(image.height)
    img += ' data-fl-original-src' + image.url + '">\n'
    yield img
    yield '\t</figure>\n'
    yield ']]></content:encoded>\n'


def generate_channel(store_id, page_id, url):
    store = Store.objects.get(id=store_id)

    page = Page.objects.get(id=page_id)

    yield '<title>' + page.name + '</title>\n'
    yield '<link>' + url + '</link>\n'
    yield '<description></description>\n'
    yield '<language>en-us</language>\n'
    yield '<atom:link rel="self" href="' + url + FEED_NAME + '" xmlns="http://www.w3.org/2005/Atom"/>\n'
    yield '<atom:link rel="hub" href="http://second-funnel.superfeedr.com/" xmlns="http://www.w3.org/2005/Atom"/>\n'

    for tile in Tile.objects.filter(feed_id=page.feed_id, template='image')[0:RESULTS]:
        yield '<item>\n'
        for tile_line in tile_to_XML(url, tile):
            yield '\t' + tile_line
        yield '</item>\n'
        time.sleep(1)


def generate_feed(store_id, page_id, url):
    yield '<rss version="2.0"\n'
    yield '\t xmlns:content="http://purl.org/rss/1.0/modules/content/"\n'
    yield '\t xmlns:dc="http://purl.org/dc/elements/1.1/"\n'
    yield '\t xmlns:media="http://search.yahoo.com/mrss/"\n'
    yield '\t xmlns:atom="http://www.w3.org/2005/Atom"\n'
    yield '\t xmlns:georss="http://www.georss.org/georss">\n'

    yield '\t<channel>\n'
    for channel_line in generate_channel(store_id, page_id, url):
        yield '\t\t' + channel_line
    yield '\t</channel>\n'
    yield '</rss>'


if __name__ == "__main__":
    main()