import json
import urlparse

from datetime import datetime
from django.http import HttpResponse, Http404
from django.conf import settings as django_settings
from django.shortcuts import render, get_object_or_404

from apps.assets.models import Page, Store, Product
from apps.scrapy.tasks import scrape_task

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
    """Async request to run a spider"""

    page = get_object_or_404(Page, url_slug=page_slug)
    # Ensure session is set up
    if not request.session.exists(request.session.session_key):
        request.session.create() 
    if not request.session.get('jobs', False):
        request.session['jobs'] = {}

    job = {
        'id': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'complete': False,
        'log_url': '',
        'summary_url': '',
        'summary': '',
    }
    # Use job start time as unique id
    request.session['jobs'].update({ job['id']: job })

    # Delayed task!
    # Could add some validation here before starting process
    # Job will be updated in the session by the task
    scrape_task.delay(category= request.GET.get('category'),
                      start_urls= json.loads(urlparse.unquote(request.GET.get('urls'))),
                      create_tiles= bool(request.GET.get('tiles') == 'true'),
                      page_slug= request.GET.get('page'),
                      session_key= request.session.session_key,
                      job_id= job['id'])

    return HttpResponse(json.dumps(job), content_type="application/json")

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
    return HttpResponse(status=204)

def log(request, page_slug, job_id):
    try:
        job = request.session['jobs'].get(job_id, None)
        return HttpResponse(json.dumps(job), content_type="application/json")
    except KeyError:
        return HttpResponse(status=400)

def summary(request, page_slug, job_id):
    try:
        job = request.session['jobs'].get(job_id, None)
        return HttpResponse(json.dumps(job), content_type="application/json")
    except KeyError:
        return HttpResponse(status=400)
