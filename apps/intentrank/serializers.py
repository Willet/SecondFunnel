from apps.api.serializers import RawSerializer


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


class ProductSerializer(RawSerializer):
    """This will dump absolutely everything in a product as JSON."""
    def get_dump_object(self, obj):
        """This will be the data used to generate the object.
        These are core attributes that every tile has.

        Also, screw you for not having any docs.
        """
        product_images = obj.product_images.all()

        data = {
            "url": obj.url,
            "price": obj.price,
            "description": obj.description,
            "name": obj.name,
            "images": [image.to_json() for image in product_images],
        }

        # if default image is missing...
        if hasattr(obj, 'default_image_id') and obj.default_image_id:
            data["default-image"] = str(obj.default_image.old_id or
                obj.default_image_id)
        elif len(product_images) > 0:
            # fall back to first image
            data["default-image"] = str(product_images[0].old_id)

        return data


class ContentSerializer(RawSerializer):

    expand_products = True

    def __init__(self, expand_products=True):
        self.expand_products = expand_products

    def get_dump_object(self, obj):
        from apps.assets.models import Product

        data = {
            'store-id': str(obj.store.old_id if obj.store else 0),
            'source': obj.source,
            'source_url': obj.source_url,
            'url': obj.url or obj.source_url,
            'author': obj.author,
            'status': obj.attributes.get('status', 'undecided'),
        }

        if obj.tagged_products.count() > 0:
            data['related-products'] = []
        else:
            data['-dbg-no-related-products'] = True
            data['-dbg-related-products'] = []

        for product in (obj.tagged_products
                            .select_related('default_image', 'product_images')
                            .all()):
            try:
                if self.expand_products:
                    data['related-products'].append(product.to_json())
                else:
                    data['related-products'].append(product.id)

            except Product.DoesNotExist as err:
                data['-dbg-related-products'].append(str(err.message))

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
            # prefixed keys are for inspection only; the hyphen is designed to
            # prevent you from using it like a js object
            '-dbg-real-tile-id': obj.old_id or obj.id,
            '-dbg-attributes': obj.attributes,
            'tile-id': obj.old_id or obj.id,
        }

        if hasattr(obj, 'template'):
            data['template'] = obj.template

        if hasattr(obj, 'prioritized'):
            data['prioritized'] = obj.prioritized

        if hasattr(obj, 'priority'):
            data['priority'] = obj.priority

        if hasattr(obj, 'attributes') and obj.attributes.get('colspan'):
            data['colspan'] = obj.attributes.get('colspan')

        return data


class ProductTileSerializer(TileSerializer):
    def get_dump_object(self, obj):
        """
        :param obj  <Tile>
        """
        data = super(ProductTileSerializer, self).get_dump_object(obj)
        try:
            data.update(obj.products
                           .select_related('product_images')[0]
                           .to_json())
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
            data.update(obj.content
                        .prefetch_related('tagged_products')
                        .select_subclasses()
                        [0]
                        .to_json())
        except IndexError as err:
            pass  # no content in this tile
        return data


class BannerTileSerializer(ContentTileSerializer):
    def get_dump_object(self, obj):
        """
        :param obj  <Tile>
        """
        data = super(BannerTileSerializer, self).get_dump_object(obj)

        # banner mode in JS is triggered by having 'redirect-url'
        redirect_url = (obj.attributes.get('redirect_url') or
                        obj.attributes.get('redirect-url'))
        if not redirect_url and obj.content.count():
            try:
                redirect_url = obj.content.select_subclasses()[0].source_url
            except IndexError as err:
                pass  # tried to find a redirect url, don't have one

        data.update({'redirect-url': redirect_url,
                     'images': [obj.attributes]})

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

        return data


YoutubeTileSerializer = VideoTileSerializer
