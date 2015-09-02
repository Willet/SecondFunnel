import json
from multiprocessing import Process
import urlparse

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

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

@login_required
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
    cat = request.POST.get('cat')
    if not cat:
        return HttpResponseBadRequest(u"Missing required data 'cat'")
    try:
        data = json.loads(urlparse.unquote(request.POST.get('cat')))
    except ValueError:
        return HttpResponseBadRequest(u"Data 'cat' was not valid json")
    urls = data.get('urls')
    if not urls:
        return HttpResponseBadRequest(u"Data 'cat' is missing 'urls', the list of urls to scrape")
    priorities = data.get('priorities', []) # Optional list of priorities
    
    if priorities and len(priorities) != len(urls):
        return HttpResponseBadRequest(u"Can't match priorities and urls because they are of different lengths")
    
    tiles = bool(request.POST.get('tiles') == 'true')
    category_name = data.get('name') # 'category_name', '' or None
    categories = [category_name] if tiles and category_name else []
    
    options = {
        'skip_tiles': not tiles,
        'refresh_images': request.POST.get('refresh_images', False)
    }

    def process(request, page, urls, options, categories, priorities):
        maintainer = PageMaintainer(page)
        maintainer.add(source_urls=urls, categories=categories, options=options)

        if categories and priorities:
            prioritize(request, page.url_slug)

    p = Process(target=process, args=[request, page, urls, options, categories, priorities])
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
            print "Setting priority of {} to '{}'".format(prod, priorities[i])
            try:
                product_tiles.filter(products__id=prod.id).update(priority=priorities[i])
            except ValueError:
                if len(priorities[i]) == 0:
                    # u''
                    pass
                else:
                    error_text = "Invalid priority '{}' for '{}'".format(priorities[i], url)
                    print error_text
                    return HttpResponseBadRequest(error_text)
    return HttpResponse(status=204)

@login_required
def log(request, page_slug, filename=None):
    return HttpResponse("<html><body>asdf3</body></html")

@login_required
def summary(request, page_slug, filename=None):
    return HttpResponse("<html><body>asdf4</body></html")
