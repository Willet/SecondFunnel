import json
import urlparse
from multiprocessing import Process

from django.db.models import Count
from django.conf import settings as django_settings
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from twisted.internet import reactor

from scrapy import log as scrapy_log, signals
from scrapy.crawler import Crawler
from scrapy.settings import CrawlerSettings
from scrapy.utils.project import get_project_settings

from apps.assets.models import Category, Page, Product, Store

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
        cat = json.loads(urlparse.unquote(request.POST.get('cat')))
        start_urls = cat['urls']
        tiles = bool(request.POST.get('tiles') == 'true')
        category = cat['name'] if tiles else None
        page = Page.objects.get(url_slug=request.POST.get('page'))
        feed = page.feed if tiles else None

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
        spider.feed_ids = [feed.id]
        spider.categories = [category]

        crawler.crawl(spider)
        scrapy_log.start()
        scrapy_log.msg(u"Starting spider with options: {}".format(opts))
        crawler.start()

        reactor.run()

        if cat['priorities'] and len(cat['priorities']) > 0:
            prioritize(request, page_slug)

    p = Process(target=process, args=[request, page.store.slug])
    p.start()
    p.join()

    return HttpResponse(status=204)

def prioritize(request, page_slug):
    """ Callback for prioritizing product tiles on page, if applicable """
    data = json.loads(urlparse.unquote(request.POST.get('cat')))
    page = Page.objects.get(url_slug=page_slug)
    store = page.store
    urls = data['urls']
    priorities = data['priorities']
    cat_name = data['name']
    category = Category.objects.get(name=cat_name, store=store)
    # Get product tiles
    product_tiles = page.feed.tiles.filter(categories__id=category.id, content=None).annotate(Count('products')).filter(products__count=1)
    # Because of a Django bug (https://code.djangoproject.com/ticket/25171), 
    # get clean QuerySet without count annotation
    product_tiles = page.feed.tiles.filter(pk__in=product_tiles.values_list('pk', flat=True))

    for i, url in enumerate(urls):
        # we assume there is only 1 product per url, but to be safe iterate over results
        prods = Product.objects.filter(url=url)
        for prod in prods:
            # filter for product tiles with this product, update priority in bulk
            product_tiles.filter(products__id=prod.id).update(priority=priorities[i])
    return HttpResponse(status=204)

def log(request, page_slug, filename=None):
    return HttpResponse("<html><body>asdf3</body></html")

def summary(request, page_slug, filename=None):
    return HttpResponse("<html><body>asdf4</body></html")
