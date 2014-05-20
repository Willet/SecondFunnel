# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.contrib.pipeline.images import ImagesPipeline
from apps.scrapy.utils import CloudinaryStore, spider_pipelined, \
    item_to_model, get_or_create, update_model


class CloudinaryPipeline(ImagesPipeline):
    """
    Enable Cloudinary storage using the ImagePipeline.

    Highly experimental, as ImagePipeline isn't really extensible at the
    moment.

    More details on the Image Pipeline here:
        http://doc.scrapy.org/en/latest/topics/images.html
    """
    def _get_store(self, uri):
        return CloudinaryStore()


class PricePipeline(object):
    @spider_pipelined
    def process_item(self, item, spider):
        item['price'] = item['price'].strip()

        if item['price'].startswith('$'):
            item['price'] = item['price'][1:]

        item['price'] = int(float(item['price']))
        return item


# This must be the last thing that we to the item
# Why? Because after we persist to the database, it doesn't matter
# What changes we make to the item.
class ItemPersistencePipeline(object):
    def process_item(self, item, spider):
        try:
            item_model = item_to_model(item)
        except TypeError:
            return item

        model, created = get_or_create(item_model)

        update_model(model, item_model)

        return item
