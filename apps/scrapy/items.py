# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
from scrapy.contrib.djangoitem import DjangoItem
from scrapy.item import Field
from apps.assets.models import Product, Content, Image, Video
from apps.scrapy.utils.serializers import store_serializer

# Fields that are not part of a Django model
# will not be saved; neat :)


# Also, fields that override existing fields don't *seem* to affect
# the underlying model field (e.g. `store` below)
class ScraperProduct(DjangoItem):
    django_model = Product
    image_urls = Field()
    images = Field()

    store = Field(serializer=store_serializer)


class ScraperContent(DjangoItem):
    django_model = Content

    store = Field(serializer=store_serializer)


class ScraperImage(ScraperContent):
    django_model = Image


class ScraperVideo(ScraperContent):
    django_model = Video
