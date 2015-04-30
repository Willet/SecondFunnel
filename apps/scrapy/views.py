import json
import urlparse

from celery import chain
from datetime import datetime
from django.http import HttpResponse, Http404
from django.conf import settings as django_settings
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import never_cache


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

@never_cache
def scrape(request, page_slug):
    """Async request to run a spider"""

    cat = json.loads(urlparse.unquote(request.POST.get('cat')))
    page = get_object_or_404(Page, url_slug=page_slug)
    # Ensure session is set up
    if not request.session.exists(request.session.session_key):
        request.session.create() 
    if not request.session.get('jobs', False):
        request.session['jobs'] = {}

    # Use job start time as unique id
    # Must define job before task is initialized to avoid race condition
    job_id = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    job = {
        'id': job_id,
        'complete': False,
        'log_url': '',
        'summary_url': '',
        'summary': {},
    }
    request.session['jobs'].update({ job['id']: job })
    request.session.save()

    task1 = scrape_task.si(category= cat['name'],
                        start_urls= cat['urls'],
                        no_priorities= bool(len(cat['priorities']) == 0),
                        create_tiles= bool(request.POST.get('tiles') == 'true'),
                        page_slug= request.POST.get('page'),
                        job_id= job_id,
                        session_key= request.session.session_key)
    task2 = prioritize_task.si(start_urls= cat['urls'], 
                             priorities= cat['priorities'],
                             job_id= job_id,
                             session_key=request.session.session_key)

    # Delayed task!
    # Could add some validation here before starting process
    # Job will be updated in the session by the task
    chain(task1, task2).delay()

    return HttpResponse(json.dumps(job), content_type="application/json")

@never_cache
def prioritize(request, page_slug):
    """callback for prioritizing tiles, if applicable"""

    cat = json.loads(urlparse.unquote(request.POST.get('cat')))
    # Use job start time as unique id
    # Must define job before task is initialized to avoid race condition
    job_id = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    job = {
        'id': job_id,
        'complete': False,
        'summary': {},
    }
    request.session['jobs'].update({ job['id']: job })
    request.session.save()

    task = prioritize_task.delay(start_urls= cat['urls'],
                                 priorities= cat['priorities'],
                                 job_id= job_id,
                                 session_key= request.session.session_key)


    return HttpResponse(json.dumps(job), content_type="application/json")

@never_cache
def result(request, page_slug, job_id):
    try:
        job = request.session['jobs'].get(job_id, None)
        return HttpResponse(json.dumps(job), content_type="application/json")
    except KeyError:
        return HttpResponse(status=400)
