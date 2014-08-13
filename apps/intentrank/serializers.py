from apps.api.serializers import RawSerializer
from apps.utils.functional import find_where


class IRSerializer(RawSerializer):
    MEMCACHE_PREFIX = 'ir'
    MEMCACHE_TIMEOUT = 0  # use db cache


class FeedSerializer(RawSerializer):
    """Turns tiles in a feed (usually, feed.tiles.all()) into a JSON object.

    :attribute _current the current object in the queryset
    """
    def __init__(self, tiles=None):
        if tiles:
            self.tiles = tiles

    def serialize(self, queryset=None, **options):
        tiles = queryset
        if not tiles and self.tiles:
            tiles = self.tiles
        if not tiles:
            raise ValueError("A QuerySet object must be supplied")
        return super(FeedSerializer, self).serialize(queryset=tiles, **options)

    @property
    def json(self, **options):
        return self.serialize(**options)

    def get_dump_object(self, obj):
        data = self._current
        return data


class ProductSerializer(IRSerializer):
    """This will dump absolutely everything in a product as JSON."""
    def get_dump_object(self, obj):
        """This will be the data used to generate the object.
        These are core attributes that every tile has.
        """
        product_images = list(obj.product_images.all())

        data = {
            "url": obj.url,
            # products don't *always* have skus
            # -- nor are they unique
            # -- nor are they necessarily numbers
            "sku": getattr(obj, "sku", ""),
            "price": obj.price,
            "description": obj.description,
            "details": obj.details,
            "name": obj.name,
        }

        data.update(obj.attributes)

        if obj.attributes.get('product_images_order'):
            # if image ordering is explicitly given, use it
            product_images = [find_where(product_images, i) for i in
                              obj.attributes.get('product_images_order', [])]
        elif hasattr(obj, 'default_image_id') and obj.default_image_id:
            # if default image is missing...
            data["default-image"] = str(obj.default_image.id or
                obj.default_image_id)
            data["orientation"] = obj.default_image.orientation

            try:
                idx = product_images.index(obj.default_image)
                product_images = [obj.default_image] + \
                                 product_images[:idx] + \
                                 product_images[idx+1:]
            except ValueError:  # that's right default image not in list
                pass  # bail ordering
        elif len(product_images) > 0:
            # fall back to first image
            data["default-image"] = str(product_images[0].id)
            data["orientation"] = product_images[0].orientation

        data["images"] = [image.to_json() for image in product_images]

        if not "orientation" in data:
            data["orientation"] = "portrait"

        return data


class ProductImageSerializer(IRSerializer):
    """This dumps some fields from the image as JSON."""
    def get_dump_object(self, obj):
        """This will be the data used to generate the object."""
        data = {
            "format": obj.file_type or "jpg",
            "type": "image",
            "dominant-color": obj.dominant_color or "transparent",
            "url": obj.url,
            "id": obj.id,
            "orientation": obj.orientation,
        }

        return data


class ContentSerializer(IRSerializer):

    def get_dump_object(self, obj):
        from apps.assets.models import Product

        data = {
            'id': str(obj.id),
            'store-id': str(obj.store.id if obj.store else 0),
            'source': obj.source,
            'source_url': obj.source_url,
            'url': obj.url or obj.source_url,
            'author': obj.author,
            'status': obj.status,
        }

        if obj.tagged_products.count() > 0:
            data['tagged-products'] = []

        for product in obj.tagged_products.filter(in_stock=True):
            try:
                data['tagged-products'].append(product.to_json())
            except Product.DoesNotExist as err:
                data['-dbg-tagged-products'].append(str(err.message))

        return data


class ImageSerializer(ContentSerializer):
    """This dumps some fields from the image as JSON."""
    def get_dump_object(self, obj):
        """This will be the data used to generate the object."""
        from apps.assets.models import default_master_size

        data = super(ImageSerializer, self).get_dump_object(obj)
        data.update({
            "format": obj.file_type or "jpg",
            "type": "image",
            "dominant-color": obj.dominant_color or "transparent",
            "url": obj.url,
            "id": obj.id,
            "status": obj.status,
            "sizes": obj.attributes.get('sizes', {
                'width': obj.width or '100%',
                'height': obj.height or '100%',
            }),
            "orientation": obj.orientation,
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
        })

        if hasattr(obj, 'attributes'):
            if obj.attributes.get('username'):
                data['username'] = obj.attributes.get('username')

        return data


class TileSerializer(IRSerializer):
    """This will dump absolutely everything in a tile as JSON."""

    def __call__(self, tile_class):
        """Returns a subclass of the tile serializer if you already know it."""
        return globals()[tile_class.capitalize() + self.__class__.__name__]

    def get_dump_object(self, obj):
        """This will be the data used to generate the object.
        These are core attributes that every tile has.
        """
        data = {
            # prefixed keys are for inspection only; the hyphen is designed to
            # prevent you from using it like a js object
            'tile-id': obj.id,
        }

        if hasattr(obj, 'template'):
            data['template'] = obj.template

        if hasattr(obj, 'prioritized'):
            data['prioritized'] = obj.prioritized

        if hasattr(obj, 'priority'):
            data['priority'] = obj.priority

        if hasattr(obj, 'attributes') and obj.attributes.get('colspan'):
            data['colspan'] = obj.attributes.get('colspan')

        if hasattr(obj, 'attributes') and obj.attributes.get('facebook-ad'):
            data['facebook-ad'] = obj.attributes.get('facebook-ad')

        return data


class ProductTileSerializer(TileSerializer):
    def get_dump_object(self, obj):
        """
        :param obj  <Tile>
        """
        data = super(ProductTileSerializer, self).get_dump_object(obj)
        try:
            data.update(obj.products.all()[0].to_json())
            data['product-ids'] = [x.id for x in obj.products.all()]
        except IndexError as err:
            pass  # no products in this tile
        return data


class ContentTileSerializer(TileSerializer):
    def get_dump_object(self, obj):
        """
        :param obj  <Tile>
        """
        data = super(ContentTileSerializer, self).get_dump_object(obj)
        try:
            data.update(obj.content.select_subclasses()[0].to_json())
            data['content-ids'] = [x.id for x in obj.content.all()]
        except IndexError as err:
            pass  # no content in this tile
        return data


MegaTileSerializer = ContentTileSerializer


class BannerTileSerializer(TileSerializer):
    def get_dump_object(self, obj):
        """
        :param obj  <Tile>
        """
        data = super(BannerTileSerializer, self).get_dump_object(obj)

        redirect_url = (obj.attributes.get('redirect_url') or
                        obj.attributes.get('redirect-url'))

        if obj.content.count():
            content_serializer = ContentTileSerializer()
            data.update(content_serializer.get_dump_object(obj))

            if not redirect_url:
                try:
                    redirect_url = obj.content.select_subclasses()[0].source_url
                except IndexError as err:
                    pass  # tried to find a redirect url, don't have one
        elif obj.products.count(): # We prefer content over products
            product_serializer = ProductTileSerializer()
            data.update(product_serializer.get_dump_object(obj))

            if not redirect_url:
                try:
                    redirect_url = obj.products.all()[0].url
                except IndexError as err:
                    pass  # tried to find a redirect url, don't have one

        data.update({'redirect-url': redirect_url})

        if not 'images' in data and obj.attributes:
            data['images'] = [obj.attributes]

        return data


class ImageTileSerializer(ContentTileSerializer):
    def get_dump_object(self, obj):
        """
        :param obj  <Tile>
        """
        data = {
            'type': 'image'
        }

        data.update(super(ImageTileSerializer, self).get_dump_object(obj))

        try:
            data.update(ImageSerializer().get_dump_object(obj.content.all()[0]))
        except IndexError:
            pass

        return data


class VideoTileSerializer(ContentTileSerializer):
    def get_dump_object(self, obj):
        """
        :param obj  <Tile>
        """
        data = {
            'type': 'video'
        }

        data.update(super(VideoTileSerializer, self).get_dump_object(obj))

        try:
            video = obj.content.select_subclasses()[0]
            data.update({
                "caption": getattr(video, 'caption', ''),
                "description": getattr(video, 'description', ''),
                "original-id": video.original_id or video.id,
                "original-url": video.source_url or video.url,
                "source": getattr(video, 'source', 'youtube'),
            })
        except:
            pass # No video in this tile.

        return data


YoutubeTileSerializer = VideoTileSerializer
