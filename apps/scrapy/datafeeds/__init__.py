import inspect

import apps.scrapy.datafeeds as dfs

def find_datafeed(name):
    datafeeds = inspect.getmembers(dfs, inspect.isclass)

    matches = [ obj if getattr(obj, 'name', None) == name for obj in datafeeds ]
    if matches:
        return matches[0]
    else:
        raise KeyError("Datafeed not found: {}".format(name))
