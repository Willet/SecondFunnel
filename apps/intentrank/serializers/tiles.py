from datetime import datetime
from django.conf import settings
import json

from apps.utils.functional import find_where, get_image_file_type, may_be_json

from .utils import IRSerializer, SerializerError


""" Serializers for tile models """


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

    def get_dump_model(self, model):
        """ shortcut for calling a serializer on a model """
        return model.serializer().get_dump_object(model)

    def get_separated_content(self, tile):
        """ Gets content in json-dict sorted by class
        returns {
            'images': assets.Image's (inc gif)
            'videos': assets.Video's
            'reviews': assets.Review's
        }
        """
        data = {}
        # convert to json
        for (k, v) in tile.separated_content.items():
            data[k] = [self.get_dump_model(c) for c in v]
           
        return data

    def get_dump_first_content_of(self, cls, tile):
        """ Return content json of first content of cls """
        content = tile.get_first_content_of(cls)
        return self.get_dump_model(content)

class ProductTileSerializer(TileSerializer):
    def get_dump_object(self, product_tile):
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
            product = self.get_dump_model(product_tile.products.first())
        except AttributeError:
            raise SerializerError('Product tile has no products')

        data = super(ProductTileSerializer, self).get_dump_object(product_tile)
        data.update({
            'product': product,
            'images': product['images'],
            'default-image': product['default-image'],
            'tagged-products': product['tagged-products'],
        })
        return data


class ContentTileSerializer(TileSerializer):
    def get_dump_object(self, content_tile):
        """
        Content is mostly an abstract class, not intended for regular use
        Just dumps of all content

        returns {
            'images': [ all images ]
            'videos': [ all videos ]
            ...
        }
        """
        data = super(ContentTileSerializer, self).get_dump_object(content_tile)
        data.update(self.get_separated_content(content_tile))
        return data


class ImageTileSerializer(ContentTileSerializer):
    def get_dump_object(self, image_tile):
        """
        returns {
            'default-image': image
            'tagged-products': [ image tagged-products ]
            ...
        }
        """
        from apps.assets.models import Image # lazy import avoids circular reference
        try:
            # cleanly handles subclasses (ie: Gif uses GifSerializer)
            image = self.get_dump_first_content_of(Image, image_tile)
        except LookupError:
            raise SerializerError('Image tile must be tagged with an image')

        data = super(TileSerializer, self).get_dump_object(image_tile)
        data.update({
            'default-image': image,
            'tagged-products': image['tagged-products']
        })
        return data


GifTileSerializer = ImageTileSerializer


class VideoTileSerializer(TileSerializer):
    def get_dump_object(self, video_tile):
        """
        returns {
            'video': video
            'tagged-products': [ video tagged-products ]
            ...
        }
        """
        from apps.assets.models import Video # lazy import avoids circular reference
        try:
            video = self.get_dump_first_content_of(Video, video_tile)
        except LookupError:
            raise SerializerError('Video tile must be tagged with a video')

        data = super(TileSerializer, self).get_dump_object(video_tile)
        data.update({
            'video': video,
            'tagged-products': video['tagged-products']
        })
        return data


YoutubeTileSerializer = VideoTileSerializer


class BannerTileSerializer(TileSerializer):
    def get_dump_object(self, banner_tile):
        """
        returns {
            'redirect-url':
            'image': image or product product-image
            ...
        }
        """
        from apps.assets.models import Image # lazy import avoids circular reference
        redirect_url = (banner_tile.attributes.get('redirect_url') or
                        banner_tile.attributes.get('redirect-url'))
        if not redirect_url:
            raise SerializerError('Banner tile must have redirect url')

        # Needs one image
        # We prefer content over products
        if banner_tile.content.count():
            try:
                image = self.get_dump_first_content_of(Image, banner_tile)
            except LookupError:
                raise SerializerError('Banner tile expecting content to be an image')
        else:
            product = banner_tile.products.first() # Could return None
            try:
                image = self.get_dump_model(product.default_image)
            except AttributeError:
                # fall back to first image
                try:
                    image = self.get_dump_model(product.product_images.first())
                except AttributeError:
                    # Ran out of options
                    raise SerializerError('Banner tile must have an image or a product with an image')

        data = super(BannerTileSerializer, self).get_dump_object(banner_tile)
        data.update({
            'default-image': image,
            'redirect-url': redirect_url,
        })
        return data


class HeroTileSerializer(TileSerializer):
    def get_dump_object(self, hero_tile):
        """
        returns {
            'image': image
            'tagged-products': [ products OR image tagged-products ]
            ...
        }
        """
        from apps.assets.models import Image # lazy import avoids circular reference
        try:
            image = hero_tile.get_first_content_of(Image)
        except LookupError:
            raise SerializerError('Hero tile expecting content to include an image')

        products = ([self.get_dump_model(p) for p in hero_tile.products.all()] or
                    [self.get_dump_model(p) for p in image.products.all()])

        data = super(HeroTileSerializer, self).get_dump_object(hero_tile)
        data.update({
            "image": self.get_dump_model(image),
            "tagged-products": products,
        })
        return data


class HerovideoTileSerializer(TileSerializer):
    def get_dump_object(self, hero_tile):
        """
        returns {
            'video': video
            'image': image (optional)
            'tagged-products': [ products OR video tagged-products OR image tagged-products ]
            ...
        }
        """
        from apps.assets.models import Image, Video # lazy import avoids circular reference
        try:
            video = hero_tile.get_first_content_of(Video)
        except LookupError:
            raise SerializerError('Herovideo tile expecting content to include a video')
        try:
            image = hero_tile.get_first_content_of(Image)
        except LookupError:
            # optional
            image = None
        
        products = ([self.get_dump_model(p) for p in hero_tile.products.all()] or
                    [self.get_dump_model(p) for p in video.products.all()] or
                    ([self.get_dump_model(p) for p in image.products.all()] if image else []))

        data = super(HeroTileSerializer, self).get_dump_object(hero_tile)
        data.update({
            "video": self.get_dump_model(video),
            "tagged-products": products,
        })
        if image:
            data['image'] = self.get_dump_model(image)
        return data

