import inspect

import apps.scrapy.datafeeds as datafeeds

def find_datafeed(name):
    dfs = inspect.getmembers(datafeeds, inspect.isclass)

    matches = [ obj if getattr(obj, 'name', None) == name for obj in dfs ]
    if matches:
        return matches[0]
    else:
        raise KeyError("Datafeed not found: {}".format(name))
