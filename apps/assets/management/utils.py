""" A collection of commands to make managing pages easier

Intended to be run from a shell"""

import csv
import pprint
import random

from django.core.exceptions import ObjectDoesNotExist, ValidationError, MultipleObjectsReturned
from django.db import transaction, models
from django.db.models.signals import post_save

from apps.assets.models import Category, Feed, Page, Product, Tile
from apps.assets.signals import tile_saved
from apps.assets.utils import disable_tile_serialization
from apps.intentrank.serializers import SerializerError



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
                if p.is_placeholder:
                    t.placeholder = True
                    t.save()
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

@disable_tile_serialization
def update_tiles_ir_cache(tiles):
    """
    Updates the ir_cache of tiles. Does not run full clean!

    Returns: <list> of <tuple>(Tile, Error) for failed updates
    """
    dts = []
    for t in tiles:
        try:
            # "manually" update tile ir cache
            ir_cache, updated = t.update_ir_cache() # sets tile.ir_cache
            if updated:
                models.Model.save(t, update_fields=['ir_cache']) # skip full_clean
            print "{}: updated".format(t)
        except SerializerError as e:
            print "\t{}: {}".format(t, e)
            dts.append((t, e))
        except ValidationError as e:
            print "\t{}: {}".format(t, e)
            dts.append((t, e))
    return dts

def remove_product_tiles_from_page(page_slug, prod_url_id_list, fake=False):
    """
    Deletes all product tiles in page that contain a product in prod_list

    prod_list: list of product identifiers that would be in the URL
    fake: if True, nothing is deleted

    Ex: remove_product_tiles_from_page("halloween", ["PRO-23545"])
    """
    fake_str = "FAKE: " if fake else ''
    page = Page.objects.get(url_slug=page_slug)
    for prod in prod_url_id_list:
        try:
            ps = Product.objects.filter(url__contains=prod)
        except Product.DoesNotExist:
            print "{}No tiles containing {}".format(fake_str, prod)
        else:
            for p in ps:
                tiles = p.tiles.filter(feed=page.feed, template="product")
                print "{}Deleting {} tiles containing {}".format(fake_str, tiles.count(), prod)
                if not fake:
                    tiles.delete()
