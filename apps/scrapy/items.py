# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
from scrapy.item import Field
from scrapy_djangoitem import DjangoItem

from apps.assets.models import Product, Content, Image, Video
from apps.scrapy.utils.serializers import store_serializer

# Fields that are not part of a Django model
# will not be saved; neat :)
class ScraperBase(DjangoItem):
    force_skip_tiles = Field()
    instance = Field() # for passing the created instance through the pipeline


# Also, fields that override existing fields don't *seem* to affect
# the underlying model field (e.g. `store` below)
class ScraperProduct(ScraperBase):
    django_model = Product # Automatically populates assets.Product fields
    image_urls = Field()
    images = Field()
    created = Field()
    tag_with_products = Field()
    content_id_to_tag = Field()
    store = Field(serializer=store_serializer)


class ScraperContent(ScraperBase):
    django_model = Content # Automatically populates assets.Content fields
    created = Field()
    tag_with_products = Field()
    content_id = Field()
    store = Field(serializer=store_serializer)


class ScraperImage(ScraperContent):
    django_model = Image # Automatically populates assets.Image fields


class ScraperVideo(ScraperContent):
    django_model = Video # Automatically populates assets.Video fields
