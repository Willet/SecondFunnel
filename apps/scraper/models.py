from django.db import models

from apps.assets.models import Store


class BaseScraper(models.Model):
    name = models.CharField(max_length=255)
    classname = models.CharField(max_length=255)

    class Meta:
        abstract = True


class ListScraper(BaseScraper):
    pass


class DetailScraper(BaseScraper):
    pass


class StoreScraper(models.Model):
    store = models.ForeignKey(Store)
    list_url = models.CharField(max_length=500)

    list_scraper = models.ForeignKey(ListScraper)
    detail_scraper = models.ForeignKey(DetailScraper)

    scrape_interval = models.IntegerField()


class SitemapListScraper(ListScraper):
    regex = models.CharField(max_length=255)


class PythonListScraper(ListScraper):
    script = models.TextField()


class PythonDetailScraper(DetailScraper):
    script = models.TextField()
