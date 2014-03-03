import json

from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers.json import Serializer as JSONSerializer
from django.core.serializers.python import Serializer as PythonSerializer


class RawSerializer(JSONSerializer):
    """This removes the square brackets introduced by the JSONSerializer."""
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
        return {
            # prefixed keys are for inspection only; the hyphen is designed to
            # prevent you from using it like a js object
            '-dbg-real-tile-id': obj.old_id or obj.id,
            '-dbg-attributes': obj.attributes,
            'tile-id': obj.old_id or obj.id,
            'template': obj.template,
            'prioritized': obj.prioritized,
        }


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
        return {
            # prefixed keys are for inspection only; the hyphen is designed to
            # prevent you from using it like a js object
            '-dbg-real-tile-id': obj.old_id or obj.id,
            '-dbg-attributes': obj.attributes,
            'tile-id': obj.old_id or obj.id,
            'template': obj.template,
            'prioritized': obj.prioritized,
        }


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
        data = super(VideoTileSerializer, self).get_dump_object(obj)

        data["original-id"] = obj.original_id or obj.id
        data["original-url"] = obj.source_url or obj.url

        return data


YoutubeTileSerializer = VideoTileSerializer
