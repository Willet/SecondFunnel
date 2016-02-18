from scrapy.loader import ItemLoader, Identity
from scrapy.loader.processors import TakeFirst, Compose, Join

from .misc import sanitize_html
from .processors import DefaultValue, MergeDicts

"""
ItemLoader's are used by spiders
"""

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

    name_in = Compose(TakeFirst(), unicode.strip)

    description_in = Compose(Join(), unicode.strip, sanitize_html)

    details_in = Compose(Join(), sanitize_html)

    attributes_out = Compose(DefaultValue(lambda: {}), MergeDicts())

    image_urls_out = Identity()


class ScraperContentLoader(ItemLoader):

    default_output_processor = TakeFirst()

    name_in = Compose(TakeFirst(), unicode.strip)

    description_in = Compose(Join(), sanitize_html)

    details_in = Compose(Join(), sanitize_html)

    attributes_out = Compose(DefaultValue(lambda: {}), MergeDicts())
