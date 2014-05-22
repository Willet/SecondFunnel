import socket

from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import View

from apps.assets.models import Feed, Store
from apps.utils import async, get_processes


class ScrapeNowView(View):
    """Scrape a single url without going into Jenkins."""
    stores = Store.objects.all()
    feeds = Feed.objects.all()
    hostname = socket.gethostname()

    @method_decorator(login_required)
    @method_decorator(never_cache)
    def get(self, request):
        """The "Add URL" UI"""
        return render_to_response('scraper/index.html', {
            "hostname": self.hostname,
            "stores": self.stores,
            "feeds": self.feeds,
        })

    @method_decorator(login_required)
    @method_decorator(never_cache)
    def post(self, request):
        """The submission controller"""

        attributes = {
            "hostname": self.hostname,
            "stores": self.stores,
            "feeds": self.feeds,
            "msg": "If valid, the URL will be scraped.",
        }

        if not request.POST.get('store-id'):
            return HttpResponse(status=400)

        running_processes = get_processes()
        for process in running_processes:
            if "phantomjs" in process:
                attributes['msg'] = "The scraper is currently busy. " \
                                    "Please try again later."
                return render_to_response('scraper/index.html', attributes)

        kwds = {"store-id": request.POST.get('store-id')}
        if request.POST.get('url'):
            kwds.update({"url": request.POST.get('url')})
        if request.POST.get('feed-id'):
            kwds.update({"feed-id": request.POST.get('feed-id')})

        self._run_scraper(**kwds)

        return render_to_response('scraper/index.html', attributes)

    def _run_scraper(self, **kwds):
        @async
        def later():
            return call_command("scraper", **kwds)
        return later()
