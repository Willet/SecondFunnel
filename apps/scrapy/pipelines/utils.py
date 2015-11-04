from collections import defaultdict
import logging

from apps.scrapy.utils.djangotools import get_or_create


class SimpleModelCache(object):
    """
    A simple module level cache
    """
    def __init__(self, model):
        self.model = model
        self.cache = defaultdict(dict)

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
