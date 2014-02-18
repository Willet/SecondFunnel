#!/usr/bin/env python

from apps.assets.models import Store
from apps.contentgraph.models import get_contentgraph_data

stores = []


def import_stores():

    for store in get_contentgraph_data('/store'):
        if not 'name' in store:
            continue
        if not 'slug' in store:
            continue
        if 1 == store['id']: # becasue 1 is a test store, not a real store
            continue
        stores.append(store)
        store_psql = Store(name=store['name'], slug=store['slug'],
                           description=store.get('description'))
        store_psql.save()


if __name__ == "__main__":
    import_stores()
