import inspect

from .surlatable import SurLaTableDatafeed

""" DEPRECATED: downloads XML files from CJ & updates projects """

datafeeds = { 'surlatable': SurLaTableDatafeed }

def find_datafeed(name):
    try:
        return datafeeds[name]
    except KeyError:
        raise KeyError("Datafeed not found: {}".format(name))
