from datetime import datetime
from django.conf import settings
import json

from apps.assets.models import Image, Video, Review
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
        return model.serializer().get_dump_object(model)

    def get_separated_content(self, tile):
        """ Returns object with content sorted into images & videos 
        Update as more content models are invented
        """
        contents = tile.content.select_subclasses()
        images = [self.get_dump_model(image) for image in contents if isinstance(image, Image)]
        videos = [self.get_dump_model(video) for video in contents if isinstance(video, Video)]
        reviews = [self.get_dump_model(review) for review in contents if isinstance(review, Review)]
        data = {}
        if images:
            # covers Image & Gif
            data["images"] = images
        if videos:
            data["videos"] = videos
        if reviews:
            data["reviews"] = reviews    
        return data

    def get_first_content_of(self, cls, tile):
        contents = tile.content.select_subclasses()
        try:
            return next(c for c in contents if isinstance(c, cls))
        except StopIteration:
            raise LookupError


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
                image = product.default_image.to_json()
            except AttributeError:
                # fall back to first image
                try:
                    image = product.product_images.first().to_json()
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
        try:
            image = self.get_dump_first_content_of(Image, hero_tile)
        except LookupError:
            raise SerializerError('Hero tile expecting content to include an image')

        products = ([product.to_json for product in hero_tile.products.all()] or
                    [product.to_json for product in image.products.all()])

        data = super(HeroTileSerializer, self).get_dump_object(hero_tile)
        data.update({
            "image": image,
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
        try:
            video = self.get_dump_first_content_of(Video, hero_tile)
        except LookupError:
            raise SerializerError('Herovideo tile expecting content to include a video')
        try:
            image = self.get_dump_first_content_of(Image, hero_tile)
        except LookupError:
            # optional
            image = None
        
        products = ([p.to_json for p in hero_tile.products.all()] or
                    [p.to_json for p in video.products.all()] or
                    ([p.to_json for p in image.products.all()] if image else []))

        data = super(HeroTileSerializer, self).get_dump_object(hero_tile)
        data.update({
            "video": video,
            "tagged-products": products,
        })
        if image:
            data['image'] = image
        return data

