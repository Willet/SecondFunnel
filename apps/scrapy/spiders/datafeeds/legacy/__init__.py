import inspect

from .surlatable import SurLaTableDatafeed
from .bodyshop import BodyShopDatafeed

""" DEPRECATED: downloads XML files from CJ & updates projects """

datafeeds = { 'surlatable': SurLaTableDatafeed,
   			  'bodyshop':  BodyShopDatafeed }

def find_datafeed(name):
    try:
        return datafeeds[name]
    except KeyError:
        raise KeyError("Datafeed not found: {}".format(name))
