from django.http import HttpResponse
from django.views.generic import View
from django.core.management import call_command


class ScrapeNowView(View):
    """Scrape a single url without going into Jenkins."""
    def get(self, request):
        """The "Add URL" UI"""
        return HttpResponse()

    def post(self, request):
        """The submission controller"""
        kwds = {"store-id": 4, "url": ""}
        call_command("scraper", **kwds)
