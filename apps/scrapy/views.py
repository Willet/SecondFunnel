import json
import urlparse
from multiprocessing import Process

from django.http import HttpResponse, Http404
from django.conf import settings as django_settings
from django.shortcuts import render, get_object_or_404
from twisted.internet import reactor

from scrapy import log as scrapy_log, signals
from scrapy.crawler import Crawler
from scrapy.settings import CrawlerSettings
from scrapy.utils.project import get_project_settings

from apps.assets.models import Page, Store, Product

stores = [{'name': store.name,'pages': store.pages.all()} for store in Store.objects.all()]

def index(request):
    """"Home" page.  does nothing."""

    data = {
        'stores': stores,
    }
    return render(request, 'index.html', data)

def page(request, page_slug):
    """This page is where scrapers are run from"""

    page = get_object_or_404(Page, url_slug=page_slug)
    data = {
        'page': page,
        'stores': stores,
    }
    return render(request, 'page.html', data)

def scrape(request, page_slug):
    """callback for running a spider"""

    page = get_object_or_404(Page, url_slug=page_slug)
    def process(request, store_slug):
        category = request.GET.get('category')
        start_urls = json.loads(urlparse.unquote(request.GET.get('urls')))
        tiles = bool(request.GET.get('tiles') == 'true')
        feeds = [Page.objects.get(url_slug=request.GET.get('page')).feed.id] if tiles else []
        opts = {
            'recreate_tiles': False,
            'skip_images': False,
            'skip_tiles': not tiles,
        }

        # set up standard framework for running spider in a script
        settings = get_project_settings()
        crawler = Crawler(settings)
        crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
        crawler.configure()

        spider = crawler.spiders.create(store_slug, **opts)
        spider.start_urls = start_urls
        spider.categories = [category] if category else []
        spider.feed_ids = feeds

        crawler.crawl(spider)
        scrapy_log.start()
        scrapy_log.msg(u"Starting spider with options: {}".format(opts))
        crawler.start()

        reactor.run()

    p = Process(target=process, args=[request, page.store.slug])
    p.start()
    p.join()

    return HttpResponse(status=204)

def prioritize(request, page_slug):
    """callback for prioritizing tiles, if applicable"""

    cat = json.loads(urlparse.unquote(request.GET.get('cat')))
    urls = cat['urls']
    priorities = cat['priorities']
    for i, url in enumerate(urls):
        prods = Product.objects.filter(url=url)
        for prod in prods:
            for tile in prod.tiles.all():
                tile.priority = priorities[i]
                tile.save()
    return HttpResponse(status=404)

def log(request, page_slug, filename=None):
    return HttpResponse("<html><body>asdf3</body></html")

def summary(request, page_slug, filename=None):
    return HttpResponse("<html><body>asdf4</body></html")
