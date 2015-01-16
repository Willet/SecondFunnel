from datetime import datetime
from django.conf import settings
import json

from apps.api.serializers import RawSerializer
from apps.utils.functional import find_where, may_be_json, get_image_file_type


class IRSerializer(RawSerializer):
    MEMCACHE_PREFIX = 'ir'
    MEMCACHE_TIMEOUT = 0  # use db cache


class FeedSerializer(IRSerializer):
    def get_dump_object(self, feed):
        return {
            'id': str(feed.id),
            'algorithm': feed.feed_algorithm,
        }


class StoreSerializer(IRSerializer):
    """Generates the PAGES_INFO.store key."""
    def get_dump_object(self, store):
        default_page = getattr(store, 'default_page', None)
        try:
            default_page_name = default_page.url_slug
        except AttributeError:
            default_page_name = None
        return {
            'id': str(store.id),
            # required for store-specific themes
            'slug': store.slug or "store",
            'name': store.name or "Store",
            'displayName': getattr(store, 'display_name', ''),  # optional
            'defaultPageName': default_page_name,
        }


class PageSerializer(IRSerializer):
    """Generates the PAGES_INFO.page key."""
    def get_dump_object(self, page):
        data = {
            'id':                   getattr(page, 'intentrank_id', page.id),
            # provided by campaign manager
            'name':                 getattr(page, 'name', ''),
            'slug':                 getattr(page, 'url_slug', ''),
            'layout':               getattr(page, 'layout', 'hero'),
            'description':          getattr(page, 'description', ''),
            # for verifying the original upload date of a static campaign
            'pubDate':              str(datetime.now().isoformat()),
            'gaAccountNumber':      getattr(page, 'ga_account_number', settings.GOOGLE_ANALYTICS_PROPERTY),
            # categories format: [{
            #                     "desktopHeroImage":"__img_url__.png"
            #                     "displayName":"For Her",
            #                     "mobileHeroImage":"__img_url__.jpg",
            #                     "name":"for-her",
            #                   },
            #                   { ... }]
            'categories':           may_be_json(page, 'categories', list),
            'mobileCategories':     may_be_json(page, 'mobileCategories', list),
            'stickyCategories':     getattr(page, 'stickyCategories', False),
            # a string indicating if there should be a home button & category home is
            'categoryHome':         getattr(page, 'categoryHome', ''),
            # expected format: ["facebook", "twitter", "pinterest", "tumblr"]
            'socialButtons':        may_be_json(page, 'socialButtons', list),
            'showSharingCount':     getattr(page, 'showSharingCount', False),
            'openLinksInNewWindow': getattr(page, 'openLinksInNewWindow', True),
            'tiles': {
                'openTileInHero':       getattr(page, 'tiles', {}).get('openTileInHero', False),
                'openProductTileInPDP': getattr(page, 'tiles', {}).get('openProductTileInPDP', False),
                # expected format: {'image': True, 'youtube': True, 'banner': False, 'product': False}
                'wideableTemplates':    getattr(page, 'tiles', {}).get('wideableTemplates', None),
                # image tile width can be randomized
                'imageTileWideProb':    getattr(page, 'tiles', {}).get('imageTileWideProb', 0.5),
            },
            'masonry': {
                'transitionDuration': getattr(page, 'masonry', {}).get('transitionDuration', '0.4s'),
                # minimum number of columns on desktop for masonry
                'minDesktopColumns':  getattr(page, 'masonry', {}).get('minDesktopColumns', 2),
                # currently unused:
                'maxColumnCount':     getattr(page, 'column_count', 4),
                # minimum number of columns to show on mobile for masonry
                'minMobileColumns':   getattr(page, 'masonry', {}).get('minMobileColumns', 2),
                'forceGrid':          getattr(page, 'masonry', {}).get('forceGrid', True),
                'tileAspectRatio':    getattr(page, 'masonry', {}).get('tileAspectRatio', 0.7),
                'heightRange':        getattr(page, 'masonry', {}).get('heightRange', 0.6),
            },
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
        data = getattr(page, 'theme_settings', {})

        # normalize: enableTracking
        enable_tracking = getattr(page, 'enable_tracking', True)
        if not isinstance(enable_tracking, bool):
            enable_tracking = bool(enable_tracking == 'true')

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
            'campaign': getattr(page, 'intentrank_id', page.id),
            'overlayButtonColor': getattr(page, 'overlay_button_color', ''),
            'overlayMobileButtonColor': getattr(page, 'overlay_mobile_button_color', ''),
            'disableBannerRedirectOnMobile': getattr(page, 'disable_banner_redirect_on_mobile', False),
            'mobileTabletView': getattr(page, 'mobile_table_view', False),
            'conditionalSocialButtons': getattr(page, 'conditional_social_buttons', {}),
            'urlParams': getattr(page, 'url_params', {}),

            # optional; default: true
            'enableTracking': enable_tracking,
            # optional. controls how often tiles are wide.
            'imageTileWide': getattr(page, 'image_tile_wide', 0.0),
            # minimum width a Cloudinary image can have  TODO: magic number
            'minImageWidth': getattr(page, 'minImageWidth', 450),
            # minimum height a Cloudinary image can have  TODO: magic number
            'minImageHeight': getattr(page, 'minImageHeight', 100),

            # default: undefined
            'featured': featured_tile,

            # DEPRECATED (use intentRank:results)
            'IRResultsCount': 10,
            # DEPRECATED (use intentRank:url)
            'IRSource': getattr(page, 'ir_base_url', '/intentrank'),
            # DEPRECATED (use intentRank:results)
            'IRAlgo': algorithm,
            # DEPRECATED (use intentRank:tileSet)
            'IRTileSet': getattr(page, 'IRTileSet', kwargs.get('tile_set', '')),
            # DEPRECATED (use intentRank:reqNum)
            'IRReqNum': 0,

            # DEPRECATED (use page:gaAccountNumber)
            'gaAccountNumber': getattr(page, 'ga_account_number', settings.GOOGLE_ANALYTICS_PROPERTY),

            'keen': {
                'projectId': settings.KEEN_CONFIG['projectId'],
                'writeKey': settings.KEEN_CONFIG['writeKey'],
            },

            # {[tileId: num,]}
            'resultsThreshold': getattr(page, 'results_threshold', None),

            # JS now fetches its own initial results
            'initialResults': [],
            # Should be moved to a new class
            'ad': {
                'forceTwoColumns':    getattr(page, 'forceTwoColumns', False),
                'columnWidth':        getattr(page, 'columnWidth', 240),
                # this is actually the slug of the associated page '/slug_name'
                # this should be a Ad Model attribute like 'associated_page'
                'tilePopupUrl':       getattr(page, 'tile_popup_url', ''),
                'tiles': {
                    'openTilesInPreview':    getattr(page, 'tiles', {}).get('openTilesInPreview', False),
                    'openProductTilesInPDP': getattr(page, 'tiles', {}).get('openProductTileInPDP', False),
                }
            }
        })

        # fill keys not available to parent serializer
        data['intentRank'].update({
            'url': getattr(page, 'ir_base_url', '/intentrank'),
            'algorithm': algorithm,  # optional
            'tileSet': kwargs.get('tile_set', ''),
        })

        if hasattr(page, 'tests'):
            data.update({
                'tests': page.tests,
            })

        return data


class ProductSerializer(IRSerializer):
    """This will dump absolutely everything in a product as JSON."""
    def get_dump_object(self, product):
        """This will be the data used to generate the object.
        These are core attributes that every tile has.
        """
        product_images = list(product.product_images.all())

        data = {
            "url": product.url,
            # products don't *always* have skus
            # -- nor are they unique
            # -- nor are they necessarily numbers
            "sku": getattr(product, "sku", ""),
            "price": product.price,
            "description": product.description,
            "details": product.details,
            "name": product.name,
            "similar-products": [],
        }

        data.update(product.attributes)

        if product.attributes.get('product_images_order'):
            # if image ordering is explicitly given, use it
            for i in product.attributes.get('product_images_order', []):
                try:
                    product_images.append(find_where(product_images, i))
                except ValueError:
                    pass  # could not find matching product image
        elif hasattr(product, 'default_image_id') and product.default_image_id:
            # if default image is missing...
            data["default-image"] = str(product.default_image.id or product.default_image_id)
            data["orientation"] = product.default_image.orientation

            try:
                idx = product_images.index(product.default_image)
                product_images = [product.default_image] + \
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

        for product in product.similar_products.filter(in_stock=True):
            try:
                data['similar-products'].append(product.to_json())
            except:
                pass

        return data


class ProductImageSerializer(IRSerializer):
    """This dumps some fields from the image as JSON."""
    def get_dump_object(self, product_image):
        """This will be the data used to generate the object."""
        data = {
            "format": product_image.file_type or "jpg",
            "type": "image",
            "dominant-color": product_image.dominant_color or "transparent",
            "url": product_image.url,
            "id": product_image.id,
            "orientation": product_image.orientation,
        }

        return data


class ContentSerializer(IRSerializer):

    def get_dump_object(self, content):
        data = {
            'id': str(content.id),
            'store-id': str(content.store.id if content.store else 0),
            'source': content.source,
            'source_url': content.source_url,
            'url': content.url or content.source_url,
            'author': content.author,
            'status': content.status,
        }

        if content.tagged_products.count() > 0:
            data['tagged-products'] = []

        for product in content.tagged_products.filter(in_stock=True):
            try:
                data['tagged-products'].append(product.to_json())
            except Exception as err:
                data['-dbg-tagged-products'].append(str(err.message))

        return data


class ImageSerializer(ContentSerializer):
    """This dumps some fields from the image as JSON."""
    def get_dump_object(self, image):
        """This will be the data used to generate the object."""
        from apps.assets.models import default_master_size

        ext = get_image_file_type(image.url)

        data = super(ImageSerializer, self).get_dump_object(image)
        data.update({
            "format": ext or "jpg",
            "type": "image",
            "dominant-color": getattr(image, "dominant_color", "transparent"),
            "url": image.url,
            "id": image.id,
            "status": image.status,
            "sizes": image.attributes.get('sizes', {
                'width': getattr(image, "width", '100%'),
                'height': getattr(image, "height", '100%'),
            }),
            "orientation": getattr(image, "orientation", "portrait"),
        })

        return data


class GifSerializer(ContentSerializer):
    """This dumps some fields from the image as JSON."""
    def get_dump_object(self, gif):
        """This will be the data used to generate the object."""
        from apps.assets.models import default_master_size

        ext = get_image_file_type(gif.url)

        data = super(GifSerializer, self).get_dump_object(gif)
        data.update({
            "format": ext or "gif",
            "type": "gif",
            "dominant-color": getattr(gif, "dominant_color", "transparent"),
            "url": gif.url,
            "id": gif.id,
            "status": gif.status,
            "sizes": gif.attributes.get('sizes', {
                'width': getattr(gif, "width", '100%'),
                'height': getattr(gif, "height", '100%'),
            }),
            "orientation": getattr(gif, "orientation", "portrait"),
            "baseImageURL": gif.baseImageURL
        })

        return data


class VideoSerializer(ContentSerializer):
    """This will dump absolutely everything in a product as JSON."""
    def get_dump_object(self, video):

        data = super(VideoSerializer, self).get_dump_object(video)

        data.update({
            "caption": getattr(video, 'caption', ''),
            "description": getattr(video, 'description', ''),
            "original-id": video.original_id or video.id,
            "original-url": video.source_url or video.url,
            "source": getattr(video, 'source', 'youtube'),
        })

        if hasattr(video, 'attributes'):
            if video.attributes.get('username'):
                data['username'] = video.attributes.get('username')

        return data


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

        if hasattr(tile, 'prioritized'):
            data['prioritized'] = tile.prioritized

        if hasattr(tile, 'priority'):
            data['priority'] = tile.priority

        data.update(tile.attributes)

        return data


class ProductTileSerializer(TileSerializer):
    def get_dump_object(self, product_tile):
        """
        :param product_tile  <Tile>
        """
        data = super(ProductTileSerializer, self).get_dump_object(product_tile)
        try:
            data.update(product_tile.products.all()[0].to_json())
            data['product-ids'] = [x.id for x in product_tile.products.all()]
        except IndexError:
            pass  # no products in this tile
        return data


class ContentTileSerializer(TileSerializer):
    def get_dump_object(self, content_tile):
        """
        :param content_tile  <Tile>
        """
        data = super(ContentTileSerializer, self).get_dump_object(content_tile)
        try:
            data.update(self.serializer_model().get_dump_object(content_tile.content.select_subclasses()[0]))
            data['content-ids'] = [x.id for x in content_tile.content.all()]
        except IndexError:
            pass  # no content in this tile
        return data


MegaTileSerializer = ContentTileSerializer


class BannerTileSerializer(TileSerializer):
    def get_dump_object(self, banner_tile):
        """
        :param banner_tile  <Tile>
        """
        data = super(BannerTileSerializer, self).get_dump_object(banner_tile)

        redirect_url = (banner_tile.attributes.get('redirect_url') or
                        banner_tile.attributes.get('redirect-url'))

        if banner_tile.content.count():
            content_serializer = ContentTileSerializer()
            data.update(content_serializer.get_dump_object(banner_tile))

            if not redirect_url:
                try:
                    redirect_url = banner_tile.content.select_subclasses()[0].source_url
                except IndexError:
                    pass  # tried to find a redirect url, don't have one
        elif banner_tile.products.count(): # We prefer content over products
            product_serializer = ProductTileSerializer()
            data.update(product_serializer.get_dump_object(banner_tile))

            if not redirect_url:
                try:
                    redirect_url = banner_tile.products.all()[0].url
                except IndexError:
                    pass  # tried to find a redirect url, don't have one

        data.update({'redirect-url': redirect_url})

        if not 'images' in data and banner_tile.attributes:
            data['images'] = [banner_tile.attributes]

        return data


class ImageTileSerializer(ContentTileSerializer):
    serializer_model = ImageSerializer


class GifTileSerializer(ContentTileSerializer):
    serializer_model = GifSerializer


class VideoTileSerializer(ContentTileSerializer):
    def get_dump_object(self, video_tile):
        """
        :param video_tile  <Tile>
        """
        data = {
            'type': 'video'
        }

        data.update(super(VideoTileSerializer, self).get_dump_object(video_tile))

        try:
            video = video_tile.content.select_subclasses()[0]
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
