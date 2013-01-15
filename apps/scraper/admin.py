from django.contrib import admin

from apps.scraper.models import (ListScraper, DetailScraper,
    StoreScraper, SitemapListScraper, PythonListScraper, PythonDetailScraper)

admin.site.register(ListScraper)
admin.site.register(DetailScraper)
admin.site.register(StoreScraper)
admin.site.register(SitemapListScraper)
admin.site.register(PythonListScraper)
admin.site.register(PythonDetailScraper)
