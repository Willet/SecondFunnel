from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.views.generic import View
from django.core.management import call_command

from apps.utils import async


class ScrapeNowView(View):
    """Scrape a single url without going into Jenkins."""
    def get(self, request):
        """The "Add URL" UI"""
        return render_to_response('scraper/index.html')

    def post(self, request):
        """The submission controller"""
        if not request.POST.get('store-id'):
            return HttpResponse(status=400)

        kwds = {"store-id": request.POST.get('store-id')}
        if request.POST.get('url'):
            kwds.update({"url": request.POST.get('url')})

        self._run_scraper(**kwds)

        return render_to_response('scraper/index.html', {
            "msg": "If valid, the URL will be scraped."
        })

    def _run_scraper(self, **kwds):
        @async
        def later():
            return call_command("scraper", **kwds)
        return later()
