import json
import urlparse

from datetime import datetime
from django.http import HttpResponse, Http404
from django.conf import settings as django_settings
from django.shortcuts import render, get_object_or_404

from apps.assets.models import Page, Store, Product
from apps.scrapy.tasks import scrape_task, prioritize_task

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

    cat = json.loads(urlparse.unquote(request.POST.get('cat')))
    page = get_object_or_404(Page, url_slug=page_slug)
    # Ensure session is set up
    if not request.session.exists(request.session.session_key):
        request.session.create() 
    if not request.session.get('jobs', False):
        request.session['jobs'] = {}

    # Delayed task!
    # Could add some validation here before starting process
    # Job will be updated in the session by the task
    task = scrape_task.delay(category= cat['name'],
                             start_urls= cat['urls'],
                             priorities= cat['priorities'],
                             create_tiles= bool(request.POST.get('tiles') == 'true'),
                             page_slug= request.POST.get('page'),
                             session_key= request.session.session_key)

    job = {
        'id': task.task_id,
        'started': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'complete': False,
        'log_url': '',
        'summary_url': '',
        'summary': '',
    }

    # Use job start time as unique id
    request.session['jobs'].update({ job['id']: job })
    request.session.save()

    return HttpResponse(json.dumps(job), content_type="application/json")

def prioritize(request, page_slug):
    """callback for prioritizing tiles, if applicable"""

    cat = json.loads(urlparse.unquote(request.POST.get('cat')))
    urls = cat['urls']
    priorities = cat['priorities']
    prioritize_task(urls, priorities)

    return HttpResponse(status=204)

def result(request, page_slug, job_id):
    try:
        job = request.session['jobs'].get(job_id, None)
        return HttpResponse(json.dumps(job), content_type="application/json")
    except KeyError:
        return HttpResponse(status=400)
