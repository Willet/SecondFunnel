from scrapy.contracts import ContractsManager
from scrapy.http import Request
from scrapy.selector import SelectorList
from scrapy.utils.python import get_spec

from apps.scrapy.utils.misc import monkeypatch_method


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

# MonkeyPatch SelectorList to add useful methods
@monkeypatch_method(SelectorList)
def extract_first(self):
    items = iter(self.extract())
    return next(items, '')

@monkeypatch_method(SelectorList)
def re_first(self, regex):
    items = iter(self.re(regex))
    return next(items, '')

@monkeypatch_method(ContractsManager)
def from_method(self, method, results):
    """
    Copied from `scrapy.contracts.ContractManager`.
    """
    contracts = self.extract_contracts(method)
    if contracts:
        # calculate request args
        args, kwargs = get_spec(Request.__init__)
        kwargs['callback'] = method
        for contract in contracts:
            kwargs = contract.adjust_request_args(kwargs)

        # create and prepare request
        args.remove('self')
        if set(args).issubset(set(kwargs)):
            # Willet: All that we do is modify these two lines to access the
            # `request_cls` from the spider if it exists.
            req_cls = getattr(method.im_self, 'request_cls', Request)
            request = req_cls(**kwargs)

            # execute pre and post hooks in order
            for contract in reversed(contracts):
                request = contract.add_pre_hook(request, results)
            for contract in contracts:
                request = contract.add_post_hook(request, results)

            return request
