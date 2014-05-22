from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils.decorators import method_decorator
from django.views.generic import View

from apps.assets.models import Feed, Store
from apps.utils import async


class ScrapeNowView(View):
    """Scrape a single url without going into Jenkins."""
    stores = Store.objects.all()
    feeds = Feed.objects.all()

    @method_decorator(login_required)
    def get(self, request):
        """The "Add URL" UI"""
        return render_to_response('scraper/index.html', {
            "stores": self.stores,
            "feeds": self.feeds,
        })

    @method_decorator(login_required)
    def post(self, request):
        """The submission controller"""

        if not request.POST.get('store-id'):
            return HttpResponse(status=400)

        kwds = {"store-id": request.POST.get('store-id')}
        if request.POST.get('url'):
            kwds.update({"url": request.POST.get('url')})
        if request.POST.get('feed-id'):
            kwds.update({"feed-id": request.POST.get('feed-id')})

        self._run_scraper(**kwds)

        return render_to_response('scraper/index.html', {
            "stores": self.stores,
            "feeds": self.feeds,
            "msg": "If valid, the URL will be scraped."
        })

    def _run_scraper(self, **kwds):
        @async
        def later():
            return call_command("scraper", **kwds)
        return later()
