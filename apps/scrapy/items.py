# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
from scrapy.contrib.djangoitem import DjangoItem
from scrapy.item import Field, Item
# from experiment.experiment.models import Product, Content


class ScraperProduct(Item):
    # django_model = Product
    name = Field()
    price = Field()
    description = Field()
    store = Field()

    # Any additional fields that are not part of the Django model
    # Will not be saved; neat :)
    image_urls = Field()
    images = Field()

    review_text = Field()
    reviewer_name = Field()
    reviewer_img = Field()


class ScraperContent(DjangoItem):
    # django_model = Content
    pass