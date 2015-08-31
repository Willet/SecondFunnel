from apps.scrapy.spiders import SecondFunnelCrawlScraper as SFScraper
from apps.utils.functional import autodiscover_module_classes


def get_spider(name):
    """ Find spider in this module with attribute name """
    try:
       return next(iter([spider for spider in \
                         autodiscover_module_classes(__name__, __path__, baseclass=SFScraper) \
                         if spider.name == name]))
    except StopIteration:
        raise LookupError("Can't find spider in <module {}> with name = '{}'".format(__name__, name))


DOWNLOAD_HANDLERS = {
    'http': 'scrapy_webdriver.download.WebdriverDownloadHandler',
    'https': 'scrapy_webdriver.download.WebdriverDownloadHandler',
}
SPIDER_MIDDLEWARES = {
    'scrapy_webdriver.middlewares.WebdriverSpiderMiddleware': 543,
}
# Or any other from selenium.webdriver or 'your_package.CustomWebdriverClass'
# or an actual class instead of a string.
WEBDRIVER_BROWSER = 'PhantomJS'
# Optional passing of parameters to the webdriver
WEBDRIVER_OPTIONS = {
    'service_args': [
        '--debug=true', '--load-images=false', '--webdriver-loglevel=debug'
    ],
}
# http://doc.scrapy.org/en/latest/topics/item-pipeline.html#activating-an-item-pipeline-component
ITEM_PIPELINES = {
    # 1's - Validation
    'apps.scrapy.pipelines.ForeignKeyPipeline': 1,
    'apps.scrapy.pipelines.ValidationPipeline': 3,
    'apps.scrapy.pipelines.DuplicatesPipeline': 5,
    # 10 - Sanitize and generate attributes
    'apps.scrapy.pipelines.PricePipeline': 11,
    'apps.scrapy.pipelines.ContentImagePipeline': 12,
    # 40 - Persistence-related
    'apps.scrapy.pipelines.ItemPersistencePipeline': 40,
    'apps.scrapy.pipelines.AssociateWithProductsPipeline': 41,
    'apps.scrapy.pipelines.TagPipeline': 42,
    'apps.scrapy.pipelines.ProductImagePipeline': 47,
    # 50 - 
    'apps.scrapy.pipelines.TileCreationPipeline': 50,
    'apps.scrapy.pipelines.SimilarProductsPipeline': 52,
    # 90 - Scrape job control
    'apps.scrapy.pipelines.PageUpdatePipeline': 99,
}
