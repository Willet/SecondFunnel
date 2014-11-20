from importlib import import_module  # this line makes me lol for some reason

from django.core.management.base import BaseCommand
from scrapy.cmdline import execute

from apps.assets.models import Feed, Page

class Command(BaseCommand):
	help = """Rescrapes all products in a given page.
	Usage:
	python manage.py update_db <url_slug> [...<url_slug>] [--tile_template=<tile_template>]

	url_slug
		Url slug of the page to rescrape.  (No pages specified means do nothing.)

	tile_template  # DOES NOT WORK YET
		Whether to create new tiles for scraped products if they don't already exist.
		If provided, create tiles with the specified template. Currently
		just creates product tiles.
	"""


	def handle(self, *args, **kwargs):
		for arg in args:
			page = Page.objects.get(url_slug=arg)
			store_name = page.store.name.lower()
			feed = page.feed

			start_urls = []
			for tile in feed.tiles.all():
				if tile.product:
					start_urls.append(tile.product.url)
				for content in tile.content.all():
					for prod in content.tagged_products.all():
						start_urls.append(prod.url)
			start_urls = set(start_urls)

			module = import_module('apps.scrapy.spiders.' + store_name)
			Spider = self.get_spider(module)
			separator = getattr(Spider, "start_urls_separator", ",")

			scrapy_args = [
				'scrapy',
				'crawl',
				Spider.name,
				'-a', 'start_urls={}'.format(separator.join(start_urls))
			]

			if kwargs.get('tile_template'):
				scrapy_args += [
					'-a', 'feed_ids={}'.format(feed.id),
					'-a', 'tile_template={}'.format(kwargs['tile_template'])
				]
			print scrapy_args
			execute(scrapy_args)

	def get_spider(self, module):
		contents = dir(module)
		contents.remove('SecondFunnelCrawlScraper')
		for i in contents:
			if issubclass(getattr(module, i), module.SecondFunnelCrawlScraper):
				return getattr(module, i)

		raise NameError("No such spider: ", module.__name__)
