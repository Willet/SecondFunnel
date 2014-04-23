"""
list of filters that act on a tile and returns true or false
(see https://docs.python.org/2/library/functions.html#filter)

For faster processing time, tiles ought to have all related fields prefetched
and selected.
"""
from functools import partial


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
