from datetime import datetime
from django.conf import settings
from django.db.models.loading import get_model
import json

from apps.utils.functional import find_where, get_image_file_type, may_be_json

from .utils import IRSerializer, SerializerError


""" Serializers for tile models

To avoid circular imports, it utilizes django model name strings like 'assets.Image'
"""


class TileSerializer(IRSerializer):
    """This will dump absolutely everything in a tile as JSON."""

    def __call__(self, tile_class):
        """Returns a subclass of the tile serializer if you already know it."""
        return globals()[tile_class.capitalize() + self.__class__.__name__]

    def get_dump_object(self, tile):
        """This will be the data used to generate the object.
        These are core attributes that every tile has.
        """
        data = {
            # prefixed keys are for inspection only; the hyphen is designed to
            # prevent you from using it like a js object
            'tile-id': tile.id,
        }
        if hasattr(tile, 'template'):
            data['template'] = tile.template

        if hasattr(tile, 'priority'):
            data['priority'] = tile.priority

        data.update(tile.attributes)

        return data

    def get_dump_separated_content(self, tile):
        """ Gets content in json-dict sorted by class
        returns {
            'images': assets.Image's (including assets.Gif)
            'videos': assets.Video's
            'reviews': assets.Review's
        }
        """
        data = {}
        # convert to json
        for (k, v) in tile.separated_content.items():
            data[k] = [c.to_json() for c in v]
           
        return data  

    def get_dump_first_content_of(self, django_cls_str, tile):
        """ Return json-dict of first content of type django_cls_str

        Note: we use django class strings (ex: 'assets.Image') to avoid circular
        import errors.

        raises: LookupError if no content of type found
        """
        # get_model deprecated in Django 1.7, will need to be refactored
        cls = get_model(*django_cls_str.rsplit('.',1))
        content = tile.get_first_content_of(cls).to_json()
        return content


class ProductTileSerializer(TileSerializer):
    def get_dump_object(self, tile):
        """
        returns {
            'product': product
            'images': [ product-images ]
            'default-image': product-image
            'tagged-products': [ product similar-products ]
            ...
        }
        """
        try:
            # Product tile should only have 1 product
            product = tile.products.first().to_json()
        except AttributeError:
            raise SerializerError('Product tile has no products')

        data = super(ProductTileSerializer, self).get_dump_object(tile)
        data.update({
            'product': product,
            'images': product['images'],
            'default-image': product['default-image'],
            'tagged-products': product['tagged-products'],
        })
        return data


class ContentTileSerializer(TileSerializer):
    def get_dump_object(self, tile):
        """
        Content is mostly an abstract class, not intended for regular use
        Just dumps of all content

        returns {
            'images': [ all images ]
            'videos': [ all videos ]
            ...
        }
        """
        data = super(ContentTileSerializer, self).get_dump_object(tile)
        data.update(self.get_dump_separated_content(tile))
        return data


class ImageTileSerializer(ContentTileSerializer):
    contenttype = 'assets.Image'

    def get_dump_object(self, tile):
        """
        returns {
            'default-image': image
            'tagged-products': [ products OR image tagged-products ]
            ...
        }
        """
        try:
            # cleanly handles subclasses (ie: Gif uses GifSerializer)
            image = self.get_dump_first_content_of(self.contenttype, tile)
        except LookupError:
            raise SerializerError('Image tile must be tagged with an image')

        products = ([p.to_json() for p in tile.products.all()] or
                    image['tagged-products'])

        data = super(TileSerializer, self).get_dump_object(tile)
        data.update({
            'default-image': image,
            'tagged-products': products,
        })
        return data


class GifTileSerializer(ImageTileSerializer):
    contenttype = 'assets.Gif'


class VideoTileSerializer(TileSerializer):
    contenttype = 'assets.Video'

    def get_dump_object(self, tile):
        """
        returns {
            'video': video
            'tagged-products': [ products OR video tagged-products ]
            ...
        }
        """
        try:
            video = self.get_dump_first_content_of(self.contenttype, tile)
        except LookupError:
            raise SerializerError('Video tile must be tagged with a video')
        products = ([p.to_json() for p in tile.products.all()] or
                    video['tagged-products'])

        data = super(VideoTileSerializer, self).get_dump_object(tile)
        data.update({
            'video': video,
            'tagged-products': products,
        })
        return data


YoutubeTileSerializer = VideoTileSerializer


class BannerTileSerializer(TileSerializer):
    contenttype = 'assets.Image'

    def get_dump_object(self, tile):
        """
        returns {
            'redirect-url':
            'default-image': image OR product product-image
            ...
        }
        """
        redirect_url = (tile.attributes.get('redirect_url') or
                        tile.attributes.get('redirect-url'))
        if not redirect_url:
            raise SerializerError('Banner tile must have redirect url')

        # Needs one image
        # We prefer content over products
        if tile.content.count():
            try:
                image = self.get_dump_first_content_of(self.contenttype, tile)
            except LookupError:
                raise SerializerError('Banner tile expecting content to be an image')
        else:
            product = tile.products.first() # Could return None
            try:
                image = product.default_image.to_json()
            except AttributeError:
                # fall back to first image
                try:
                    image = product.product_images.first().to_json()
                except AttributeError:
                    # Ran out of options
                    raise SerializerError('Banner tile must have an image or a product with an image')

        data = super(BannerTileSerializer, self).get_dump_object(tile)
        data.update({
            'default-image': image,
            'redirect-url': redirect_url,
        })
        return data


class HeroTileSerializer(TileSerializer):
    contenttype = 'assets.Image'

    def get_dump_object(self, tile):
        """
        returns {
            'default-image': image
            'tagged-products': [ products OR image tagged-products ]
            ...
        }
        """
        try:
            image = self.get_dump_first_content_of(self.contenttype)
        except LookupError:
            raise SerializerError('Hero tile expecting content to include an image')

        products = ([p.to_json() for p in tile.products.all()] or
                    image['tagged-products'])

        data = super(HeroTileSerializer, self).get_dump_object(tile)
        data.update({
            "default-image": image,
            "tagged-products": products,
        })
        return data


class HerovideoTileSerializer(TileSerializer):
    contenttype = 'assets.Video'

    def get_dump_object(self, tile):
        """
        returns {
            'video': video
            'image': image (optional)
            'tagged-products': [ products OR video tagged-products OR image tagged-products ]
            ...
        }
        """
        try:
            video = self.get_dump_first_content_of(self.contenttype, tile)
        except LookupError:
            raise SerializerError('Herovideo tile expecting content to include a video')
        try:
            image = self.get_dump_first_content_of('assets.Image', tile)
        except LookupError:
            # optional
            image = {}
        
        products = ([p.to_json() for p in tile.products.all()] or
                    video['tagged-products'] or image.get('tagged-products', []))

        data = super(HerovideoTileSerializer, self).get_dump_object(tile)
        data.update({
            "video": video,
            "tagged-products": products,
        })
        if image:
            data['image'] = image
        return data

