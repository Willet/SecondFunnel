""" A collection of commands to make managing pages easier

Intended to be run from a shell"""

import csv
import pprint

from apps.assets.models import Category, Feed, Page, Product, Tile
from django.core.exceptions import ObjectDoesNotExist, ValidationError, MultipleObjectsReturned
from django.db import transaction

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

def merge_products_with_same_url(url, store):
    ps = Product.objects.filter(url=url, store=store)
    not_placeholders = [ p for p in ps if not p.is_placeholder ]
    not_placeholders.sort(key=lambda p: p.created_at, reverse=True)
    # grab the most recent not placehoder, or the first placeholder
    product = not_placeholders[0] or ps[0]
    product.merge([ p for p in ps if p != product])

def update_page_from_datafeed(page):
    """ Assumes in.txt is a csv product data feed (usually provided by CJ.com)

    :param page - Page to update

    :returns - a list of results
    """
    lookup_fields = ["SKU", "NAME"]
    collect_fields = ["SKU", "NAME", "DESCRIPTION", "PRICE", "SALEPRICE", "BUYURL", "INSTOCK"]
    results = {
        'logging/errors': {},
        'logging/items dropped': [],
        'logging/items out of stock': [],
        'logging/items updated': [],
        'logging/new items': [],
    }

    def update_product(product, data):
        product.price = float(data['PRICE'])
        product.sale_price = float(data['SALEPRICE'])
        product.in_stock = True if data['INSTOCK'] == 'yes' else False
        product.attributes['cj_link'] = data['BUYURL']
        product.save()

        if not product.in_stock:
            results['logging/items out of stock'].append(product.url)
            #print 'logging/items out of stock: {}'.format(product.url)
        else:
            results['logging/items updated'].append(product.url)
            #print 'logging/items updated: {}'.format(product.url)

    lookup_table = {}
    for i in lookup_fields:
        lookup_table[i] = {}

    with open('in.txt', 'rb') as infile:
        csv_file = csv.DictReader(infile, delimiter=',')
        for row in csv_file:
            # Correct for encoding errors
            entry = { f: row[f].decode("utf-8").encode("latin1").decode("utf-8") for f in collect_fields }

            for i in lookup_fields:
                lookup_table[i][entry[i].encode('ascii', errors='ignore')] = entry

    print u"Generated lookup table's for {} products".format(len(lookup_table[lookup_fields[0]]))

    products = page.feed.get_all_products()

    print u"Found {} products for {}".format(len(products), page.url_slug)

    # Find product in product data feed & update
    with transaction.atomic():
        for product in products:
            try:
                try:
                    data = lookup_table['SKU'][product.sku]
                    if data:
                        print u"SKU match: {}".format(product.url)
                        update_product(product, data)
                except KeyError:
                    try:
                        print u"\tAttemping NAME match: {}".format(product.name.encode('ascii', errors='ignore'))
                        data = lookup_table['NAME'][product.name.encode('ascii', errors='ignore')]
                        if data:
                            print u"NAME match: {}".format(product.url)
                            update_product(product, data)
                    except KeyError:
                        # TODO: attempt fuzzy DESCRIPTION matching?
                        results['logging/items dropped'].append(product.url)
                        print 'logging/items dropped: {}'.format(product.url)
            except Exception as e:
                errors = results['logging/errors']
                msg = '{}: {}'.format(e.__class__.__name__, e)
                items = errors.get(msg, [])
                items.append(product.url)
                errors[msg] = items
                results['logging/errors'] = errors
                print 'logging/errors: {}'.format(msg)

    print "Updates saved"

    pprint.pprint({
        'logging/errors': len(results['logging/errors']),
        'logging/items dropped': len(results['logging/items dropped']),
        'logging/items out of stock': len(results['logging/items out of stock']),
        'logging/items updated': len(results['logging/items updated']),
        'logging/new items': len(results['logging/new items']),
    })

    return results
