from importlib import import_module  # this line makes me lol for some reason

from scrapy import log, signals
from twisted.internet import reactor
from django.core.management.base import BaseCommand
from scrapy.settings import CrawlerSettings
from scrapy.crawler import Crawler

from apps.assets.models import Feed, Page
from apps.scrapy import spiders

import sys
import os

class Command(BaseCommand):
	help = "Rescrapes all products in a given page.  Page url_slugs are given in the args.  (No pages specified means do nothing.)"

	def handle(self, *args, **kwargs):
		to_scrape = []  # [store_name, start_urls, feed]

		for arg in args:
			page = Page.objects.get(url_slug=arg)
			store_name = page.store.name
			feed = page.feed

			urls = [tile.product.url for tile in feed.tiles.all() if tile.product]

			to_scrape.append((store_name, urls, feed.id))

		for store_name, start_urls, feed_id in to_scrape:
			crawler = Crawler(CrawlerSettings(import_module('apps.scrapy.settings')))
			crawler.install()
			crawler.signals.connect(reactor.stop, signal=signals.spider_closed)

			module = import_module('apps.scrapy.spiders.' + store_name)
			Spider = self.get_spider(module)
			separator = getattr(Spider, "start_urls_separator", ",")

			spider = Spider(start_urls=separator.join(start_urls), feed_ids=str(feed_id))

			crawler.crawl(spider)
			crawler.start()
			log.start()
			reactor.run()

	def get_spider(self, module):
		contents = dir(module)
		contents.remove('SecondFunnelCrawlScraper')
		for i in contents:
			if issubclass(getattr(module, i), module.SecondFunnelCrawlScraper):
				return getattr(module, i)

		raise NameError("No such spider: ", module.__name__)
