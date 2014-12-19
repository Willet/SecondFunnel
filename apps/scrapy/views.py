import json
import urlparse

from django.http import HttpResponse, Http404
from django.conf import settings as django_settings
from django.shortcuts import render
from twisted.internet import reactor

from scrapy import log as scrapy_log, signals
from scrapy.crawler import Crawler
from scrapy.settings import CrawlerSettings
from scrapy.utils.project import get_project_settings

from apps.assets.models import Page, Store

stores = Store.objects.all()
def index(request):
    return render(request, 'index.html', {'stores': stores})

def store(request, store_slug):
    try:
        store = stores.get(slug=store_slug)
    except:
        raise Http404

    return render(request, 'store.html', {'store': store, 'stores': stores})

def scrape(request, store_slug):
    #from twisted.internet import reactor
    
    category = request.GET.get('category')
    urls = json.loads(urlparse.unquote(request.GET.get('urls')))
    #raise Exception(urls)
    # set up scrapy crawler
    settings = get_project_settings() 
    # CrawlerSettings()
    # settings.settings_module = django_settings.SCRAPY_SETTINGS_MODULE
    crawler = Crawler(settings)
    crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
    crawler.configure()
    #return HttpResponse(json.dumps(settings.__dict__, default=lambda x: ''), content_type="application/json")

    spider = crawler.spiders.create(store_slug)
    spider.start_urls = urls
    spider.categories = [category]
    crawler.crawl(spider)
    scrapy_log.start()
    crawler.start()

    reactor.run()


    def default(x):
        if type(x).__name__ == 'module':
            return x.__dict__.keys()
        return type(x).__name__
    #response = json.dumps(crawler.__dict__, default=default)

    response = json.dumps(crawler.stats.get_stats(), default=lambda x: "(fake)")

    return HttpResponse(response, content_type="application/json")


def log(request, store_slug, filename=None):
    return HttpResponse("<html><body>asdf3</body></html")

def summary(request, store_slug, filename=None):
    return HttpResponse("<html><body>asdf4</body></html")
