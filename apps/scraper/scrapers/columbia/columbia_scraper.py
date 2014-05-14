from apps.assets.models import Category
from apps.scraper.scrapers import ProductDetailScraper, ProductCategoryScraper


class ColumbiaProductScraper(ProductDetailScraper):
    regexs = [r'(?:https?://)?(?:www\.)?columbia\.com/(.+pd\.html.+)$']


class ColumbiaCategoryScraper(ProductCategoryScraper):
    """Actually scrapes Columbia's subcategories (where products are listed)."""
    regexs = [r'(?:https?://)?(?:www\.)?columbia\.com/(.+sc\.html.+)$']
