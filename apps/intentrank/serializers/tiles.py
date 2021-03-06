from datetime import datetime
from django.conf import settings
from django.db.models.loading import get_model
import json
import logging

from apps.utils.functional import find_where, get_image_file_type, may_be_json

from .utils import IRSerializer, SerializerError, camelize_JSON


""" Serializers for tile models

To avoid circular imports, it utilizes django model name strings like 'assets.Image'
"""


class TileSerializer(IRSerializer):
    """Abstract base class for all tile serializers."""

    def __call__(self, tile_template):
        """Returns a subclass of the tile serializer if you already know it.

        ie: for template 'image' -> returns ImageTileTemplate
        """
        try:
            return globals()[tile_template.capitalize() + self.__class__.__name__]
        except KeyError:
            return DefaultTileSerializer

    def get_dump_object(self, tile):
        raise NotImplementedError

    def get_core_attributes(self, tile):
        """ This will be the data used to generate the object.
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

        data.update(camelize_JSON(tile.attributes))

        return data

    def get_dump_separated_content(self, tile):
        """ Gets content in json-dict sorted by class
        returns {
            'images': assets.Image's (including assets.Gif) OR 'image': ...
            'videos': assets.Video's OR 'video': ...
            'reviews': assets.Review's OR 'review': ...
        }
        """
        data = {}
        content = tile.separated_content
        # copy over images, videos and reviews as json dicts
        # if there is just 1 of something, use its singular name image / video / review
        if len(content['images']):
            if len(content['images']) == 1:
                data['default-image'] = content['images'][0].to_json()
            else:
                data['images'] = [c.to_json() for c in content['images']]
        if len(content['videos']):
            if len(content['videos']) == 1:
                data['video'] = content['videos'][0].to_json()
            else:
                data['videos'] = [c.to_json() for c in content['videos']]
        if len(content['reviews']):
            if len(content['reviews']) == 1:
                data['review'] = content['reviews'][0].to_json()
            else:
                data['reviews'] = [c.to_json() for c in content['reviews']]

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

    def get_dump_tagged_products(self, tile):
        """ Return json-dict of tile products """
        tagged_products = tile.products.filter(placeholder=False)
        if not tile.feed.store.display_out_of_stock:
            tagged_products = tagged_products.filter(in_stock=True)
        return [p.to_json() for p in tagged_products]


class DefaultTileSerializer(TileSerializer):
    """ For unknown tile templates, populate with all the content we can """
    def get_dump_object(self, tile):
        """
        returns {
            'defaultImage'/'images': image or [ images ]
            'video'/'videos': video or [ videos ]
            'review'/'reviews': review or [ reviews ]
            'tagged-products': [ products ]
        }
        """
        content = self.get_dump_separated_content(tile)
        products = self.get_dump_tagged_products(tile)

        data = self.get_core_attributes(tile)
        data.update(content)
        data.update({
            'tagged-products': products,
        })
        return data


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
            raise SerializerError(u'Product Tile #{} has no products'.format(tile.id))
        if not product['default-image']:
            raise SerializerError(u'Product Tile #{} must have a default image'.format(tile.id))

        products = product['tagged-products']

        data = self.get_core_attributes(tile)
        data.update({
            'product': product,
            'images': product['images'],
            'default-image': product['default-image'],
            'tagged-products': product['tagged-products'],
        })
        return data


class ImageTileSerializer(TileSerializer):
    contenttype = 'assets.Image'

    def get_dump_object(self, tile):
        """
        returns {
            'default-image': image
            'tagged-products': [ products OR image tagged-products ]
            ...
        }
        """
        images = tile.separated_content['images']

        defaultImageId = tile.attributes.get('defaultImage') or tile.attributes.get('default-image')
        if defaultImageId:
            try:
                image = [i.to_json() for i in images if i.id == defaultImageId][0]
            except IndexError:
                raise SerializerError(u"Image Tile #{} is not tagged with its "
                                      u"default Image #{}".format(tile.id, defaultImageId))
        else:
            try:
                # cleanly handles subclasses (ie: Gif uses GifSerializer)
                image = self.get_dump_first_content_of(self.contenttype, tile)
            except LookupError:
                raise SerializerError(u"Image Tile #{} must be tagged with an image".format(tile.id))

        products = (self.get_dump_tagged_products(tile) or image['tagged-products'])

        expandedImageId = tile.attributes.get('expandedImage') or tile.attributes.get('expanded-image')
        expandedImage = None
        if expandedImageId:
            try:
                expandedImage = [i.to_json() for i in images if i.id == expandedImageId][0]
            except IndexError:
                raise SerializerError(u"Image Tile #{} is not tagged with its "
                                      u"expanded Image #{}".format(tile.id, expandedImageId))

        mobileExpandedImageId = (tile.attributes.get('mobileExpandedImage')
                                 or tile.attributes.get('mobile-expanded-image'))
        mobileExpandedImage = None
        if mobileExpandedImageId:
            try:
                mobileExpandedImage = [i.to_json() for i in images if i.id == mobileExpandedImageId][0]
            except IndexError:
                raise SerializerError(u"Image Tile #{} is not tagged with its "
                                      u"mobile expanded Image #{}".format(tile.id, mobileExpandedImageId))

        data = self.get_core_attributes(tile)
        data.update({
            'default-image': image,
            'tagged-products': products,
        })
        if expandedImage:
            data['expandedImage'] = expandedImage
        if mobileExpandedImage:
            data['mobileExpandedImage'] = mobileExpandedImage
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
            raise SerializerError(u"Video Tile #{} must be tagged with a video".format(tile.id))

        products = (self.get_dump_tagged_products(tile) or video['tagged-products'])

        data = self.get_core_attributes(tile)
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
            'redirectUrl':
            'default-image': image OR product product-image
            ...
        }
        """
        redirect_url = (tile.attributes.get('redirect_url') or
                        tile.attributes.get('redirect-url') or
                        tile.attributes.get('redirectUrl'))

        # Needs one image
        # We prefer content over products
        if tile.content.count():
            try:
                image = self.get_dump_first_content_of(self.contenttype, tile)
            except LookupError:
                raise SerializerError(u"Banner Tile #{} expecting "
                                      u"content to be an image".format(tile.id))
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
                    raise SerializerError(u"Banner Tile #{} must have an image "
                                          u"or a product with an image".format(tile.id))

        data = self.get_core_attributes(tile)
        data['default-image'] = image
        if redirect_url:
            data['redirectUrl'] = redirect_url
        return data


class CollectionTileSerializer(TileSerializer):
    contenttype = 'assets.Image'

    def get_dump_object(self, tile):
        """
        Attributes specify a default image id (and optionally an expanded image id) that is also
        tagged to the tile.  Default image is used for the tile view and expanded image for a pop-up.

        returns {
            'default-image': image
            'expandedImage': image (optional)
            'tagged-products': [ products ]
        }
        """
        images = tile.separated_content['images']
        defaultImageId = (tile.attributes.get('defaultImage') or tile.attributes.get('default-image')
                          or tile.attributes.get('default_image'))
        if defaultImageId:
            # expecting it to be an ID of one of the tagged content
            try:
                image = [i.to_json() for i in images if i.id == defaultImageId][0]
            except IndexError:
                raise SerializerError(u"Collection Tile #{} is not tagged with its "
                                      u"default Image #{}".format(tile.id, defaultImageId))
        else:
            # Grab first tagged image
            try:
                image = self.get_dump_first_content_of(self.contenttype, tile)
            except LookupError:
                raise SerializerError(u"Collection Tile #{} expecting content to "
                                      u"include an image".format(tile.id))

        expandedImageId = tile.attributes.get('expandedImage') or tile.attributes.get('expanded-image')
        expandedImage = None
        if expandedImageId:
            try:
                expandedImage = [i.to_json() for i in images if i.id == expandedImageId][0]
            except IndexError:
                raise SerializerError(u"Collection Tile #{} is not tagged with its "
                                      u"expanded Image #{}".format(tile.id, expandedImageId))

        mobileExpandedImageId = (tile.attributes.get('mobileExpandedImage')
                                 or tile.attributes.get('mobile-expanded-image'))
        mobileExpandedImage = None
        if mobileExpandedImageId:
            try:
                mobileExpandedImage = [i.to_json() for i in images if i.id == mobileExpandedImageId][0]
            except IndexError:
                raise SerializerError(u"Collection Tile #{} is not tagged with its "
                                      u"mobile expanded Image #{}".format(tile.id, mobileExpandedImageId))

        products = self.get_dump_tagged_products(tile)

        data = self.get_core_attributes(tile)
        data.update({
            "default-image": image,
            "tagged-products": products,
        })
        if expandedImage:
            data['expandedImage'] = expandedImage
        if mobileExpandedImage:
            data['mobileExpandedImage'] = mobileExpandedImage
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
            image = self.get_dump_first_content_of(self.contenttype, tile)
        except LookupError:
            raise SerializerError(u"Hero Tile expecting content to include an image".format(tile.id))

        products = (self.get_dump_tagged_products(tile) or image['tagged-products'])

        data = self.get_core_attributes(tile)
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
            raise SerializerError(u"Herovideo Tile #{} expecting "
                                  u"content to include a video".format(tile.id))
        try:
            image = self.get_dump_first_content_of('assets.Image', tile)
        except LookupError:
            # optional
            image = {}

        products = (self.get_dump_tagged_products(tile) or video['tagged-products']
                    or image.get('tagged-products', []))

        data = self.get_core_attributes(tile)
        data.update({
            "video": video,
            "tagged-products": products,
        })
        if image:
            data['image'] = image
        return data

