# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
from scrapy.contrib.djangoitem import DjangoItem
from scrapy.item import Field, Item


class ScraperProduct(Item):
    # Fields that are not part of a Django model
    # will not be saved; neat :)

    name = Field()
    price = Field()
    description = Field()
    store = Field()

    image_urls = Field()
    images = Field()

    review_text = Field()
    reviewer_name = Field()
    reviewer_img = Field()


class ScraperContent(DjangoItem):
    pass
