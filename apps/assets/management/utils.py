""" A collection of commands to make managing pages easier

Intended to be run from a shell"""

import csv
import random
import requests
import json
from pprint import pprint

from django.core.exceptions import ObjectDoesNotExist, ValidationError, MultipleObjectsReturned
from django.db import transaction, models
from django.db.models.signals import post_save
from django.conf import settings

from apps.assets.models import Category, Feed, Page, Product, ProductImage, Tile
from apps.assets.signals import productimage_saved
from apps.assets.utils import delay_tile_serialization, disable_tile_serialization
from apps.imageservice.utils import get_public_id


def set_negative_priorities(tile_id_list):
    """Set tile priority to -1 for tiles in tile_id_list

    ex: tile_id_list= [123,234,345,...]

    Useful to get id list: <Queryset>.values_list('id', flat=True)"""
    results = u""
    with transaction.atomic():
        for i in tile_id_list:
            try:
                t = Tile.objects.get(id=i)
                t.priority = -1
                t.save()
                results += u"{} priority set to -1\n".format(t)
            except (ObjectDoesNotExist, ValidationError) as e:
                results += u"ERROR: {}: {}\n".format(i, e)
    print results

def set_priorities(tile_id_and_priority_tuple_list):
    """Set tile priority for each tile

    ex: tile_id_and_priority_tuple_list= [(123, 1), (234, 2), ...]"""
    results = u""
    with transaction.atomic():
        for (i, p) in tile_id_and_priority_tuple_list:
            try:
                t = Tile.objects.get(id=i)
                t.priority = p
                t.save()
                results += u"{} priority set to {}\n".format(t, t.priority)
            except (ObjectDoesNotExist, ValidationError) as e:
                results += u"ERROR: {}: {}\n".format(i, repr(e))
    print results

def set_default_images(tile_id_and_image_id_tuple_list):
    """Set the default image for each tile based on some unique str component in the url

    Note: a side effect is that all tiles with this product will be updated as well

    ex: tile_id_and_image_id_tuple_list= [(123, 'abc234'), (234, 'def567'), ...]"""
    results = u""
    with transaction.atomic():
        for (i, u) in tile_id_and_image_id_tuple_list:
            try:
                t = Tile.objects.get(id=i)
                p = t.products.first()
                pi = next(pi for pi in p.product_images.all() if u in pi.url)
                p.default_image = pi
                p.save()
                results += u"{} default image set to {}\n".format(p, pi)
            except (ObjectDoesNotExist, StopIteration, ValidationError) as e:
                results += u"ERROR: ({}, \"{}\"): {}\n".format(i, u, repr(e))
    print results

def generate_tiles_from_urls(feed, category, urls):
    store = feed.store
    products = []
    results = {
        'doesnotexist': [],
        'created': [],
        'updated': [],
        'error': [],
    }

    category = category if isinstance(category, Category) else \
               Category.objects.get(store=store, name=category)

    for url in urls:
        try:
            p = Product.objects.get(store=store, url=url)
        except Product.DoesNotExist:
            results['doesnotexist'].append(url)
        except MultipleObjectsReturned as e:
            results['error'].append({
                    'exception': repr(e),
                    'url': url,
                })
        else:
            try:
                tile, created = feed.add(p, category=category)
            except Exception as e:
                results['error'].append({
                    'exception': repr(e),
                    'url': url,
                })
            else:
                if created:
                    results['created'].append(url)
                else:
                    results['updated'].append(url)
    return results

def set_random_priorities(tiles, max_priority=0, min_priority=0):
    """ Randomly assign priorities to tiles using range(1:number of tiles)

    Optional: will use range(1:max_priority) or range(min_priority:max_priority)
    for priority values.
    """
    if max_priority is 0:
        max_priority = len(tiles)
    print u"Assigning priorities in range {} to {}".format(min_priority, max_priority)
    priorities = range(min_priority, max_priority)
    random.shuffle(priorities)
    with transaction.atomic():
        for t in tiles:
            t.priority = priorities.pop()
            t.save()
            print u"{} priority set to {}".format(t, t.priority)
    print u"Random priorities set for {} Tiles".format(len(tiles))

def update_dominant_color(tiles):
    """
    Updates dominant color of all the images in the provided tiles
    Chooses non-product-shot default images for all tiles provided
    """

    def get_resource_url(public_id):
        return "https:{}/resources/image/upload/{}?colors=1".format(settings.CLOUDINARY_API_URL, public_id)

    rescrape = [] # list of product urls that must be re-scraped

    with delay_tile_serialization():
        with requests.Session() as s:
            s.auth = requests.auth.HTTPBasicAuth(settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET)
            for i, t in enumerate(tiles):
                try:
                    pis = t.product.product_images.all()
                    print "{} {}: getting dominant_color for {} images".format(i, t, pis.count())
                except AttributeError:
                    print "{} {}: no product".format(i, t)
                    continue
                if not len(t.product.product_images.all()):
                    print "{}: no product images".format(t)
                    continue
                for j, pi in enumerate(pis):
                    # Download image information from cloudinary
                    public_id = get_public_id(pi.url)
                    url = get_resource_url(public_id)
                    data = s.get(url)
                    result = json.loads(data.text)
                    if "error" in result:
                        print "\t{} Error: {}".format(j, result['error']['message'])
                        rescrape.append(t.product.url)
                        continue
                    else:
                        pi.dominant_color = result['colors'][0][0]
                        pi.save()
                        print "\t{} {}".format(j, pi.dominant_color)
                # Now that product images have dominant color, update default image
                t.product.choose_lifestyle_shot_default_image()
                if t.product.default_image.is_product_shot:
                    print "Default image search failed. Chose first"
                    t.attributes['colspan'] = 1
                    t.save()

    if len(rescrape):
        print "Rescrape these product urls with {'refresh-images': True}:"
        pprint(rescrape)
    return rescrape

def remove_product_tiles_from_page(page_slug, prod_url_id_list, category=False, fake=False):
    """
    Deletes all product tiles in page that contain a product in prod_list

    prod_list: list of product identifiers that would be in the URL
    category: (optional) <str> or <Category> - remove product tiles from this category only
    fake: (optional) <bool> if True, nothing is deleted

    Ex: remove_product_tiles_from_page("halloween", ["PRO-23545"])
    """
    fake_str = "FAKE: " if fake else ''
    page = Page.objects.get(url_slug=page_slug)
    if category and isinstance(category, basestring):
        category = Category.objects.get(store=page.store, name=category)

    for prod in prod_url_id_list:
        try:
            ps = Product.objects.filter(url__contains=prod)
        except Product.DoesNotExist:
            print "{}No tiles containing {}".format(fake_str, prod)
        else:
            for p in ps:
                if category:
                    tiles = p.tiles.filter(feed=page.feed, categories=category, template="product")
                else:
                    tiles = p.tiles.filter(feed=page.feed, template="product")
                print "{}Deleting {} tiles containing {}".format(fake_str, tiles.count(), prod)
                if not fake:
                    tiles.delete()
