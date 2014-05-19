# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
from scrapy.contrib.djangoitem import DjangoItem
from scrapy.item import Field, Item
from apps.assets.models import Product

# Fields that are not part of a Django model
# will not be saved; neat :)
class ScraperProduct(DjangoItem):
    django_model = Product
    image_urls = Field()
    images = Field()

    # store_id = Field()
    #
    # name = Field()
    # description = Field()
    # details = Field()
    # url = Field()
    # sku = Field()
    # price = Field()
    #
    # product_image_id = Field
    #
    # last_scraped_at = Field()
    #
    # in_stock = Field()
    #
    # attributes = Field()


class ScraperContent(DjangoItem):
    pass
