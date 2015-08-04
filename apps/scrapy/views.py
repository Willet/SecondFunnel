import json
import urlparse
from multiprocessing import Process

from django.db.models import Count
from django.conf import settings as django_settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from twisted.internet import reactor

from scrapy import log as scrapy_log, signals
from scrapy.crawler import Crawler
from scrapy.settings import CrawlerSettings
from scrapy.utils.project import get_project_settings

from apps.assets.models import Category, Page, Product, Store
from apps.scrapy.controllers import PageMaintainer

stores = [{'name': store.name,'pages': store.pages.all()} for store in Store.objects.all()]

@login_required
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

@require_POST
@login_required
def scrape(request, page_slug):
    """callback for running a spider"""
    page = get_object_or_404(Page, url_slug=page_slug)
    def process(request, store_slug):
        cat = json.loads(urlparse.unquote(request.POST.get('cat')))
        tiles = bool(request.POST.get('tiles') == 'true')
        categories = [cat['name']] if tiles else []
        urls = cat['urls']
        page = Page.objects.get(url_slug=request.POST.get('page'))

        options = {
            'skip_tiles': not tiles,
        }

        maintainer = PageMaintainer(page)
        maintainer.add(source_urls=urls, categories=categories, options=options)

        if cat['priorities'] and len(cat['priorities']) > 0:
            prioritize(request, page_slug)

    p = Process(target=process, args=[request, page.store.slug])
    p.start()
    p.join()

    return HttpResponse(status=204)

@require_POST
@login_required
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
    product_tiles = page.feed.tiles.filter(categories__id=category.id, template='product')

    for i, url in enumerate(urls):
        # we assume there is only 1 product per url, but to be safe iterate over results
        prods = Product.objects.filter(url=url)
        for prod in prods:
            # filter for product tiles with this product, update priority in bulk
            product_tiles.filter(products__id=prod.id).update(priority=priorities[i])
    return HttpResponse(status=204)

@login_required
def log(request, page_slug, filename=None):
    return HttpResponse("<html><body>asdf3</body></html")

@login_required
def summary(request, page_slug, filename=None):
    return HttpResponse("<html><body>asdf4</body></html")
