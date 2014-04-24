"""
list of filters that act on a tile and returns true or false
(see https://docs.python.org/2/library/functions.html#filter)

For faster processing time, tiles ought to have all related fields prefetched
and selected.
"""
from functools import partial
import random


def in_stock(tile):
    """
    Returns False if the tile has no products in stock,
    or none of its content with tagged products in stock.

    Returns True otherwise.
    """
    if tile.products.count():
        for product in tile.products.all():
            if product.in_stock:
                return True

    if tile.content.count():
        for content in tile.content.all():
            if not content.tagged_products.count():
                return True
            for product in content.tagged_products.all():
                if product.in_stock:
                    return True


def pick(tile, probability=0.1):
    """
    Given this   ^   figure, return True or False, regardless of
    what that tile is.

    Useful for quickly selecting random tiles.
    """
    return random.choice([True] * 9 + [False])


def id_in(ids):
    """returns a filter that returns True if a tile has one of the given ids."""
    def filtr(tile):
        return tile.id in ids
    return filtr

def id_not_in(ids):
    """returns a filter that returns False if a tile has one of the given ids."""
    def filtr(tile):
        return not tile.id in ids
    return filtr

def prioritized(state=''):
    """returns a filter that returns True if a tile is prioritized as {state}.

    special filter: with state of 'any', any prioritized tiles will be True.
    """
    def filtr(tile):
        if state == 'any':
            if tile.prioritized != '':
                return True
        if tile.prioritized == state:
            return True
    return filtr


def order_by(tiles, *what):
    """e.g. 'date' by date, or '-date' by inverse date.

    Currently supports only one ordering.
    """
    criterion, order = what[0], 1
    if criterion[0] == '-':
        criterion, order = criterion[1:], -1

    thing = sorted(tiles, key=lambda tile: getattr(tile, criterion, None))
    if order < 0:
        return list(reversed(thing))
    return thing
