import urllib

from django.db import models

from apps.assets.models import Store, Product


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
    store = models.OneToOneField(Store, primary_key=True)
    list_url = models.CharField(max_length=500)

    list_scraper = models.ForeignKey(ListScraper)
    detail_scraper = models.ForeignKey(DetailScraper)

    scrape_interval = models.IntegerField()

    status = models.SmallIntegerField(default=0, blank=True, null=True)


class SitemapListScraper(ListScraper):
    regex = models.CharField(max_length=255)


class PythonListScraper(ListScraper):
    script = models.TextField()
    enable_javascript = models.BooleanField(default=False)
    enable_css = models.BooleanField(default=False)


class PythonDetailScraper(DetailScraper):
    script = models.TextField()
    enable_javascript = models.BooleanField(default=False)
    enable_css = models.BooleanField(default=False)


class ProductSuggestion(models.Model):
    product = models.ForeignKey(Product, related_name="suggestions")
    url = models.URLField(max_length=500)
    suggested = models.ForeignKey(Product, related_name="suggested", blank=True, null=True)


class ProductTags(models.Model):
    id = models.OneToOneField(Product,
        primary_key=True, related_name="tags", db_column="id")

    tags = models.TextField()

    class Meta:
        managed = False
        db_table = 'scraper_product_tags'

    def parsed(self):
        try:
            return dict(
                [(
                    urllib.unquote(pair.split("_")[0]),
                    urllib.unquote(pair.split("_")[1])
                ) for pair in self.tags.split()]
            )

        # in case self.tags is missing, or formatted not how we expect, etc
        except:
            return {}
