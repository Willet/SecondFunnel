import inspect

from .surlatable import SurLaTableDatafeed

datafeeds = { 'surlatable': SurLaTableDatafeed }

def find_datafeed(name):
    try:
        return datafeeds[name]
    except KeyError:
        raise KeyError("Datafeed not found: {}".format(name))
