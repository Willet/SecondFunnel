from scrapy.contrib.loader import ItemLoader, Identity
from scrapy.contrib.loader.processor import TakeFirst, Compose
from apps.scrapy.utils.misc import str_to_boolean
from apps.scrapy.utils.processors import MergeDicts


class ScraperProductLoader(ItemLoader):
    """
    Creates items via XPath or CSS expressions.

    Basically, reduces the amount of work involved in scraping items because
    the item loader can take an XPath or CSS expression and immediately load
    that into the item (or add multiple values, if the exist).

    As well, the item loader can handle custom input / output processing for
    common operations.

    More details available in the docs:
        http://doc.scrapy.org/en/latest/topics/loaders.html
    """
    default_output_processor = TakeFirst()

    attributes_out = MergeDicts()

    image_urls_out = Identity()

    in_stock_in = Compose(lambda v: v[0], str_to_boolean)
