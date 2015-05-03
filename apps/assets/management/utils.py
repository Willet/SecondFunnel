""" A collection of commands to make managing pages easier

Intended to be run from a shell"""

from apps.assets.models import *
from django.core.exceptions import ObjectDoesNotExist, ValidationError
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
                t.priority = 0
                t.save()
                results += u"{} priority set to 0\n".format(t)
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
                results += u"ERROR: {}: {}\n".format(i, e)
    print results

def set_default_images(tile_id_and_image_id_tuple_list):
    """Set the default image for each tile based on some unique str component in the url

    ex: tile_id_and_image_id_tuple_list= [(123, 'abc234'), (234, 'def567'), ...]"""
    results = u""
    with transaction.atomic():
        for (i, u) in tile_id_and_image_id_tuple_list:
            try:
                t = Tile.objects.filter(id=i)[0]
                p = t.products.all()[0]
                pi = next(pi for pi in p.product_images.all() if u in pi.url)
                p.default_image = pi
                p.save()
                results += u"{} default image set to {}\n".format(p, pi)
            except (ObjectDoesNotExist, ValidationError, IndexError) as e:
                results += u"ERROR: ({}, \"{}\"): {}\n".format(i, u, e)
    print results
