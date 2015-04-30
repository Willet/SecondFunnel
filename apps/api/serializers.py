import json

from django.core.serializers.json import Serializer as JSONSerializer
from django.utils.text import slugify
from apps.utils.models import MemcacheSetting


class RawSerializer(JSONSerializer):
    """This removes the square brackets introduced by the JSONSerializer."""
    MEMCACHE_PREFIX = 'cg'
    MEMCACHE_TIMEOUT = 60

    @classmethod
    def dump(cls, obj, skip_cache=False):
        """obj be <Model>"""
        return cls().to_json([obj], skip_cache=skip_cache)

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
        """Contrary to what the method name suggests, this

        :returns a dict.
        """
        return json.loads(self.to_str(queryset=queryset, **options))

    def to_str(self, queryset, **options):
        # single object serialization cache
        # for when an object was done more than once per request
        skip_cache = options.pop('skip_cache', False)
        if skip_cache:
            return self.serialize(queryset=queryset, **options)

        if len(queryset) == 1:
            obj = queryset[0]

            # representation already made
            if self.MEMCACHE_PREFIX == 'ir' and getattr(obj, 'ir_cache', ''):
                return getattr(obj, 'ir_cache', '')

            obj_key = "{0}-{1}-{2}".format(self.MEMCACHE_PREFIX,
                                           obj.__class__.__name__, obj.id)

            # if you have a memcache, that is
            obj_str_cache = MemcacheSetting.get(obj_key, False)
            if obj_str_cache:  # in cache, return it
                return obj_str_cache
            else:  # not in cache, save it
                obj_str = self.serialize(queryset=queryset, **options)
                MemcacheSetting.set(obj_key, obj_str,
                                    timeout=self.MEMCACHE_TIMEOUT)  # save
                return obj_str

        return self.serialize(queryset=queryset, **options)


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
            "social-buttons": "[\"tumblr\", \"pinterest\", \"facebook\"]",  # Stores don't have those anymore... just going to fake it
            "theme": obj.default_theme.template if getattr(obj, 'default_theme_id', False) else None,
            "slug": slugify(obj.name),  # major design flaw dictates that our stores don't have slugs
        }
        return data


class ProductSerializer(RawSerializer):
    """This will dump absolutely everything in a product as JSON."""
    def get_dump_object(self, obj):
        """This will be the data used to generate the object.
        These are core attributes that every tile has.
        """
        from apps.assets.models import Tile

        data = {
            "id": str(obj.id),
            "created": obj.cg_created_at,
            "last-modified": obj.cg_updated_at,
            "default-image-id": obj.default_image.id if obj.default_image else 0,
            "product-set": obj.attributes.get('product_set', 'live'),
            "image-ids": [str(o.id) for o in obj.product_images.all()],
            "available": obj.attributes.get('available', True),
            "sku": obj.sku,
            "url": obj.url,
            "price": obj.price,
            "description": obj.description,
            "name": obj.name,
            "store-id": str(obj.store.id),
        }

        tile_configs = [tile.tile_config for tile in Tile.objects.filter(
            products__id=obj.id
        )]
        data.update({
            "tile-configs": tile_configs
        })

        return data


class ContentSerializer(RawSerializer):

    def get_dump_object(self, obj):
        from apps.assets.models import Tile

        data = {
            "id": str(obj.id),
            "source": obj.source,
            "last-modified": obj.cg_updated_at,
            "created": obj.cg_created_at,
            # e.g. ImageSerializer -> 'image'
            "type": self.__class__.__name__[:self.__class__.__name__.index('Serializer')].lower(),
            "tagged-products": [str(p.id) for p in obj.tagged_products.all()],
            "url": obj.url,
            "status": obj.status,  # by default it is
        }

        if hasattr(obj, 'store'):
            data["store-id"] = str(obj.store.id)

        tile_configs = [tile.tile_config for tile in Tile.objects.filter(
            content__id=obj.id
        )]
        data.update({
            "tile-configs": tile_configs
        })

        return data


class ImageSerializer(ContentSerializer):
    """This will dump absolutely everything in a product as JSON."""
    def get_dump_object(self, obj):
        data = super(ImageSerializer, self).get_dump_object(obj)
        data.update({
            "original-url": obj.original_url or obj.url,
            "format": obj.file_type,
            "hash": getattr(obj, 'file_checksum', ''),
            "orientation": 'landscape' if obj.width > obj.height else 'portrait',
        })

        return data


class GifSerializer(ContentSerializer):
    """This will dump absolutely everything in a product as JSON."""
    def get_dump_object(self, obj):
        data = super(GifSerializer, self).get_dump_object(obj)
        data.update({
            "original-url": obj.original_url or obj.url,
            "format": obj.file_type,
            "hash": getattr(obj, 'file_checksum', ''),
            "orientation": 'landscape' if obj.width > obj.height else 'portrait',
            "gifUrl": obj.gif_url
        })

        return data


class ProductImageSerializer(RawSerializer):
    """This will dump absolutely everything in a product as JSON."""
    def get_dump_object(self, obj):

        data = {
            "id": str(obj.id),
            "product-id": str(obj.product_id) if obj.product else "-1",
            "url": obj.url,
            "original-url": obj.original_url or obj.url,
            "format": obj.file_type,
            "hash": getattr(obj, 'file_checksum', ''),
            "width": obj.width,
            "height": obj.height,
            "orientation": 'landscape' if obj.width > obj.height else 'portrait',
            "last-modified": obj.cg_updated_at,
            "created": obj.cg_created_at,
            "type": "image",
            "dominant-colour": obj.dominant_color,  # deprecated
            "dominant-color": obj.dominant_color,
        }

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
        """

        data = {
            "id": str(obj.id),
            "heroImageDesktop": obj.desktop_hero_image,
            "last-modified": obj.cg_updated_at,
            "social-buttons": obj.social_buttons,
            "theme": obj.theme.template if obj.theme else None,
            "url": obj.url_slug,
            "imageTileWide": obj.get('theme_settings',{}).get('image_tile_wide'),
            "legalCopy": obj.legal_copy,
            "shareText": obj.description,
            "created": obj.cg_created_at,
            "heroImageMobile": obj.mobile_hero_image,
            "name": obj.name,
            "layout": 'hero',
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
        """
        data = {
            "template": obj.template,
            "id": str(obj.id),
            "last-modified": obj.cg_updated_at,
            "created": obj.cg_created_at,
            "json": json.dumps(obj.to_json()),
            "prioritized": "true" if obj.prioritized else "false",
        }

        try:
            data["page-id"] = str(obj.feed.page.all()[0].id)
        except IndexError:
            # the feed doesn't belong to a page (perhaps intentionally).
            data["page-id"] = "0"

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
        data = {
            "template": obj.template,
            "id": str(obj.id),
            "is-content": "false" if obj.template == 'product' else "true",
            "last-modified": obj.cg_updated_at,
            "created": obj.cg_created_at,
            # backwards compat means any len(string)>0 counts as prioritized from before
            "prioritized": "true" if obj.prioritized else "false",
        }

        try:
            data["page-id"] = str(obj.feed.page.all()[0].id)
        except IndexError:
            # the feed doesn't belong to a page (perhaps intentionally).
            data["page-id"] = "0"

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
