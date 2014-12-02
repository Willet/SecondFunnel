import ast
from datetime import datetime
import json
from django.conf import settings

from apps.api.serializers import RawSerializer
from apps.utils.functional import find_where


class IRSerializer(RawSerializer):
    MEMCACHE_PREFIX = 'ir'
    MEMCACHE_TIMEOUT = 0  # use db cache


class FeedSerializer(IRSerializer):
    def get_dump_object(self, obj):
        return {
            'id': str(obj.id),
            'algorithm': obj.feed_algorithm,
        }


class StoreSerializer(IRSerializer):
    """Generates the PAGES_INFO.store key."""
    def get_dump_object(self, obj):
        return {
            'id': str(obj.id),
            # required for store-specific themes
            'slug': obj.slug or "store",
            'name': obj.name or "Store",
            'displayName': getattr(obj, 'display_name', ''),  # optional
        }


class PageSerializer(IRSerializer):
    """Generates the PAGES_INFO.page key."""
    def get_dump_object(self, obj):
        # string representation of [{id: 123, name: 'gap'}, ...]
        # normalize categories list/str into a list
        categories = obj.get('categories', '[]')
        if isinstance(categories, basestring):
            #noinspection PyTypeChecker
            categories = ast.literal_eval(categories)

        mobileCategories = obj.get('mobileCategories', '[]')
        if isinstance(mobileCategories, basestring):
            #noinspection PyTypeChecker
            mobileCategories = ast.literal_eval(mobileCategories)

        data = {
            'id': getattr(obj, 'intentrank_id', obj.id),
            # for verifying the original upload date of a static campaign.
            # for human use only
            'pubDate': str(datetime.now().isoformat()),

            'gaAccountNumber': getattr(obj, 'ga_account_number',
                                       settings.GOOGLE_ANALYTICS_PROPERTY),

            # provided by campaign manager
            'name': obj.name or '',
            'slug': obj.url_slug or '',
            'layout': obj.get('layout', 'hero'),

            'categories': categories,
            'mobileCategories': mobileCategories,
            'description': obj.description or '',

            # optional (defaults to 240 or 255 pixels)
            # TODO: undefined
            'columnWidth': obj.get('column_width',
                                   obj.store.get('column-width', None)),
            'maxColumnCount': obj.get('column_count', 4),
        }

        return data


class IntentRankSerializer(object):
    """Generates the PAGES_INFO.intentRank key."""
    def to_json(self):
        return {
            'results': 10,
            'reqNum': 0,  # optional
            'offset': 0,  # TODO: find a way to eliminate this variable
        }


class PageConfigSerializer(object):
    """Generates PAGES_INFO.

    This is not a subclass of Serializer as it accepts different objects
    as input.
    """
    @staticmethod
    def to_json(request, page, feed=None, store=None, algorithm=None,
                featured_tile=None, other=None):
        """
        keys in other:
        - tile_set ('product', 'content', '')
        """

        if not store:
            store = page.store

        if not feed:
            feed = page.feed

        if not algorithm:
            algorithm = 'generic'

        # custom variables (kwargs)
        kwargs = {}
        if not other:
            other = {}
        kwargs.update(other)

        # output attributes automatically (if the js knows how to use them)
        if hasattr(page, 'theme_settings'):
            data = page.theme_settings
        else:
            data = {}

        # normalize: socialButtons
        social_buttons = page.get('social_buttons', page.store.get('social-buttons'))\
            or ["facebook", "twitter", "pinterest", "tumblr"]

        if isinstance(social_buttons, basestring):
            #noinspection PyTypeChecker
            social_buttons = json.loads(social_buttons)

        # normalize: enableTracking
        enable_tracking = page.get('enable_tracking', True)
        if not isinstance(enable_tracking, bool):
            enable_tracking = (enable_tracking == 'true')

        data.update({
            'debug': settings.DEBUG,
            # no longer a setting (why would we change this?)
            'itemSelector': '.tile',

            'store': store.to_json(),
            'page': page.to_json(),
            'feed': feed.to_json(),
            'intentRank': IntentRankSerializer().to_json(),

        })

        data.update({
            # DEPRECATED (use page:id)
            'campaign': page.get('intentrank_id') or page.id,
            # DEPRECATED (use page:columnWidth)
            'columnWidth': page.get('column_width',
                page.store.get('column-width', None)),  # TODO: undefined
            # DEPRECATED (use page:maxColumnCount)
            'maxColumnCount': page.get('column_count') or 4,

            'overlayButtonColor': page.get('overlay_button_color') or '',
            'overlayMobileButtonColor': page.get('overlay_mobile_button_color') or '',
            'disableBannerRedirectOnMobile': page.get('disable_banner_redirect_on_mobile') or False,
            'mobileTabletView': page.get('mobile_table_view') or False,
            'widableTemplates': json.loads(page.get('widable_templates', 'null')),
            'socialButtons': social_buttons,

            'conditionalSocialButtons': page.get('conditional_social_buttons') or {},
            'openTileInPopup': True if page.get("open_tile_in_popup") else False,
            'tilePopupUrl': page.get('tile_popup_url') or '',
            'urlParams': page.get("url_params") or {},

            # a string or boolean indicating if there should be a home button /
            # what the home button should be
            'categoryHome': page.get('categoryHome', True),
            # optional, for social buttons (default: true)
            'showCount': True,
            # optional; default: true
            'enableTracking': enable_tracking,
            # optional. controls how often tiles are wide.
            'imageTileWide': page.get('image_tile_wide') or 0.0,
            # minimum width a Cloudinary image can have  TODO: magic number
            'minImageWidth': page.get('minImageWidth') or 450,
            # minimum height a Cloudinary image can have  TODO: magic number
            'minImageHeight': page.get('minImageHeight') or 100,
            'masonry': page.get('masonry') or {},

            # default: undefined
            'featured': featured_tile,

            # DEPRECATED (use intentRank:results)
            'IRResultsCount': 10,
            # DEPRECATED (use intentRank:url)
            'IRSource': page.get('ir_base_url') or '/intentrank',
            # DEPRECATED (use intentRank:results)
            'IRAlgo': algorithm,
            # DEPRECATED (use intentRank:tileSet)
            'IRTileSet': page.get('IRTileSet', kwargs.get('tile_set', '')),
            # DEPRECATED (use intentRank:reqNum)
            'IRReqNum': 0,

            # DEPRECATED (use page:gaAccountNumber)
            'gaAccountNumber': page.get('ga_account_number') or
                               settings.GOOGLE_ANALYTICS_PROPERTY,

            'keen': {
                'projectId': settings.KEEN_CONFIG['projectId'],
                'writeKey': settings.KEEN_CONFIG['writeKey'],
            },

            # {[tileId: num,]}
            'resultsThreshold': page.get('results_threshold', None),

            # JS now fetches its own initial results
            'initialResults': [],
        })
        data['masonry'].update({
            'transitionDuration': '0.4s',
            # minimum number of columns on desktop for masonry
            'minDesktopColumns': page.get('minDesktopColumns') or 2,
            # minimum number of columns to show on mobile for masonry
            'minMobileColumns': page.get('minMobileColumns') or 2,
        })

        # fill keys not available to parent serializer
        data['intentRank'].update({
            'url': page.get('ir_base_url') or '/intentrank',
            'algorithm': algorithm,  # optional
            # "content", "products", or anything else for both content and product
            'tileSet': kwargs.get('tile_set', ''),
        })

        if page.get('tests'):
            data.update({
                'tests': page.get('tests'),
            })

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
            "similar-products": [],
        }

        data.update(obj.attributes)

        if obj.attributes.get('product_images_order'):
            # if image ordering is explicitly given, use it
            for i in obj.attributes.get('product_images_order', []):
                try:
                    product_images.append(find_where(product_images, i))
                except ValueError:
                    pass  # could not find matching product image
        elif hasattr(obj, 'default_image_id') and obj.default_image_id:
            # if default image is missing...
            data["default-image"] = str(obj.default_image.id or obj.default_image_id)
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

        for product in obj.similar_products.filter(in_stock=True):
            try:
                data['similar-products'].append(product.to_json())
            except:
                pass

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
            except Exception as err:
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

        data.update(obj.attributes)

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
        except IndexError:
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
        except IndexError:
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
                except IndexError:
                    pass  # tried to find a redirect url, don't have one
        elif obj.products.count(): # We prefer content over products
            product_serializer = ProductTileSerializer()
            data.update(product_serializer.get_dump_object(obj))

            if not redirect_url:
                try:
                    redirect_url = obj.products.all()[0].url
                except IndexError:
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
