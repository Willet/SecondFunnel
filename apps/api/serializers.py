import json

from django.core.serializers.json import Serializer as JSONSerializer
from django.utils.text import slugify


class RawSerializer(JSONSerializer):
    """This removes the square brackets introduced by the JSONSerializer."""
    @classmethod
    def dump(cls, obj):
        """obj be <Model>"""
        return cls().to_json([obj])

    def start_serialization(self):
        if json.__version__.split('.') >= ['2', '1', '3']:
            # Use JS strings to represent Python Decimal instances (ticket #16850)
            self.options.update({'use_decimal': False})
        self._current = None
        self.json_kwargs = self.options.copy()
        self.json_kwargs.pop('stream', None)
        self.json_kwargs.pop('fields', None)

    def end_serialization(self):
        """Do not want the original behaviour (adding commas)"""
        pass

    def to_json(self, queryset, **options):
        return json.loads(self.serialize(queryset=queryset, **options))


class StoreSerializer(RawSerializer):
    def get_dump_object(self, obj):
        """This will be the data used to generate the object."""
        data = {
            "id": str(obj.id),
            "name": obj.name,
            "display_name": obj.name,  # TODO: how's this different from name?
            "public-base-url": obj.public_base_url,
            "last-modified": obj.cg_updated_at,
            "created": obj.cg_created_at,
            "social-buttons": "[\"tumblr\", \"pinterest\", \"facebook\"]",  # TODO
            "theme": obj.default_theme.template if getattr(obj, 'default_theme_id', False) else None,
            "column-width": "220",  # TODO
            "slug": slugify(obj.name),  # major design flaw dictates that our stores don't have slugs
        }
        return data


class ProductSerializer(RawSerializer):
    """This will dump absolutely everything in a product as JSON."""
    def get_dump_object(self, obj):
        """This will be the data used to generate the object.
        These are core attributes that every tile has.

        Also, screw you for not having any docs.
        """
        # product_images = obj.product_images.all()

        data = {
            "-dbg-id": str(obj.id),
            "id": str(obj.id),
            "created": obj.cg_created_at,
            "last-modified": obj.cg_updated_at,
            "default-image-id": obj.default_image.id,
            "product-set": "live",  # TODO
            "image-ids": [str(o.id) for o in obj.product_images.all()],
            "available": "true",  # TODO
            "sku": obj.sku,
            "url": obj.url,
            "price": obj.price,
            "description": obj.description,
            "name": obj.name,
            "store-id": str(obj.store.id),
            # "rescrape": "false",
            # "last-scraped": "1394775462303",
        }
        return data


class ContentSerializer(RawSerializer):

    def get_dump_object(self, obj):
        data = {
            "-dbg-id": str(obj.id),
            "id": str(getattr(obj, 'id', obj.id)),
            "source": obj.source,
            "last-modified": obj.cg_updated_at,
            "created": obj.cg_created_at,
            "store-id": str(obj.store.id),
            # e.g. ImageSerializer -> 'image'
            "type": self.__class__.__name__[:self.__class__.__name__.index('Serializer')].lower(),
            "tagged-products": [str(p.id) for p in obj.tagged_products.all()],
            "url": obj.url,
            "status": obj.status,  # by default it is
        }

        return data


class ImageSerializer(ContentSerializer):
    """This will dump absolutely everything in a product as JSON."""
    def get_dump_object(self, obj):
        data = super(ImageSerializer, self).get_dump_object(obj)
        data.update({
            "original-url": obj.original_url or obj.url,
            "format": obj.file_type,
            "hash": getattr(obj, 'file_checksum', ''),
        })

        return data


class VideoSerializer(ContentSerializer):
    """This will dump absolutely everything in a product as JSON."""
    def get_dump_object(self, obj):

        data = super(VideoSerializer, self).get_dump_object(obj)

        data.update({
            "caption": getattr(obj, 'caption', ''),
            "description": getattr(obj, 'description', ''),
            "original-id": obj.original_id or obj.id,
            "original-url": obj.source_url or obj.url,
            "source": getattr(obj, 'source', 'youtube'),
            "is-content": "true",
            "source-url": obj.source_url,
            "page-prioritized": "false",  # TODO: ?
        })

        if hasattr(obj, 'attributes'):
            if obj.attributes.get('username'):
                data['username'] = obj.attributes.get('username')

        return data


class PageSerializer(RawSerializer):
    def get_dump_object(self, obj):
        """This will be the data used to generate the object.
        These are core attributes that every tile has.

        Also, screw you for not having any docs.
        """

        data = {
            "-dbg-id": str(obj.id),
            "id": str(getattr(obj, 'id', obj.id)),
            "heroImageMobile": obj.desktop_hero_image,
            "intentrank_id": obj.intentrank_id,
            "ir_base_url": obj.ir_base_url,
            # "IRSource": obj.ir_base_url,  # TOGO
            "last-modified": obj.cg_updated_at,
            "social-buttons": obj.social_buttons,
            "theme": obj.theme.template if obj.theme else None,
            "url": obj.url_slug,
            # "ir-last-generated": "1391710019",
            # "ir-stale": "true",
            "imageTileWide": obj.theme_settings.get('image_tile_wide'),
            "created": obj.cg_created_at,
            # "last-queued-stale-tile": "1394056998",
            "heroImageDesktop": obj.mobile_hero_image,
            "name": obj.name,
            "layout": obj.template,
            "column-width": obj.column_width,
            "store-id": str(obj.store.id),
        }

        return data


class TileSerializer(RawSerializer):
    """This will dump absolutely everything in a tile as JSON."""

    def __call__(self, tile_class):
        """Returns a subclass of the tile serializer if you already know it."""
        return globals()[tile_class.capitalize() + self.__class__.__name__]

    def get_dump_object(self, obj):
        """This will be the data used to generate the object.
        These are core attributes that every tile has.

        Also, screw you for not having any docs.
        """
        data = {
            "template": obj.template,
            '-dbg-id': obj.id,
            "id": str(obj.id),
            "page-id": str(obj.feed.page.all()[0].id),  # if this fails, it deserves an exception outright
            "last-modified": obj.cg_updated_at,
            "content-ids": [
                "14035"
            ],
            "created": obj.cg_created_at,
            "json": json.dumps(obj.to_json()),
            "prioritized": "true" if obj.prioritized else "false",
        }

        if obj.content.count() > 0:
            data.update({
                "content-ids": [str(c.id) for c in obj.content.all()],
            })

        elif obj.products.count() > 0:  # content tiles with tagged products never shows tagged products
            data.update({
                "product-ids": [str(p.id) for p in obj.products.all()],
            })

        if type(obj.attributes) is dict:
            data.update(obj.attributes)

        return data


class TileConfigSerializer(RawSerializer):
    """Tile --> tileconfig json"""
    def get_dump_object(self, obj):
        data =  {
            "template": obj.template,
            "id": str(obj.id),
            "page-id": str(obj.feed.page.all()[0].id),  # if this fails, it deserves an exception outright
            "is-content": "false" if obj.template == 'product' else "true",
            "last-modified": obj.cg_updated_at,
            "created": obj.cg_created_at,
            "prioritized": str(obj.prioritized).lower(),
            # "stale": "false",  # useless
        }

        if obj.content.count() > 0:
            data.update({
                "content-ids": [str(c.id) for c in obj.content.all()],
            })

        elif obj.products.count() > 0:  # content tiles with tagged products never shows tagged products
            data.update({
                "product-ids": [str(p.id) for p in obj.products.all()],
            })

        if type(obj.attributes) is dict:
            data.update(obj.attributes)

        return data
