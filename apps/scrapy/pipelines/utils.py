from collections import defaultdict
from itertools import chain
import logging

from apps.scrapy.utils.djangotools import get_or_create


class SimpleModelCache(object):
    """
    A simple module level cache
    """
    def __init__(self, model):
        self.model = model
        self.cache = defaultdict(dict)

    def __len__(self):
        # Break store-indexed caches out and count their items
        return sum([len(indexed_items) for indexed_items in self.cache.values()])

    def add(self, item, name, store):
        # Add to cache
        self.cache[store.slug][name] = item

    def get_or_create(self, name, store):
        try:
            # Check cache
            item = self.cache[store.slug][name]
        except KeyError:
            # Get or create category
            item, created = get_or_create(self.model(name=name, store=store))
            if created:
                logging.info("Creating category '{}' for {}".format(name, store))
                item.save()
            # Add to cache
            self.cache[store.slug][name] = item
        return item

    def get(self, name, store):
        try:
            # Check cache
            item = self.cache[store.slug][name]
        except KeyError:
            # Get or create category
            item = None
        return item

    def dump_items(self):
        """
        Returns iterable list of all items stored in the cache
        """
        lists_of_items = [indexed_items.values() for indexed_items in self.cache.values()]
        return chain(*lists_of_items)
