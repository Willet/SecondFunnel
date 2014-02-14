import sys

import urllib2
import ast

from apps.assets.models import Store

headers = {'ApiKey': 'secretword'}
base_url = 'http://contentgraph-test.elasticbeanstalk.com/graph/'

stores = []


def importStores():
    store_request = urllib2.Request(base_url + 'store', None, headers)

    stores_raw = urllib2.urlopen(store_request).read()

    stores_results = ast.literal_eval(stores_raw)['results']

    for store in stores_results:
        if not 'name' in store:
            continue
        if not 'slug' in store:
            continue
        if 1 == store['id']: # becasue 1 is a test store, not a real store
            continue
        stores.append(store)
        store_psql = Store(name=store['name'], slug=store['slug'], description=store['description'])
        store_psql.save()



importStores()
