import os
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

			for url in start_urls:
				cmd = 'scrapy crawl {} -a start_urls={}'.format(store_name, url)
				if kwargs.get('tile_template'):  # don't use it
					cmd += '-a feed_ids={} -a tile_template={}'.format(feed.id, kwargs['tile_template'])
				os.system(cmd)
