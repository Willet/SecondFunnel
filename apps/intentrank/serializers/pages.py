from datetime import datetime
from django.conf import settings
import json

from apps.utils.functional import may_be_json

from .utils import IRSerializer, SerializerError


""" Serializers for models that structure for clients / pages """


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
            'gaAccountNumber':      getattr(page, 'gaAccountNumber', settings.GOOGLE_ANALYTICS_PROPERTY),
            'defaults': {
                'heroImage':        getattr(page, 'defaults', {}).get('heroImage', ''),
                'mobileHeroImage':  getattr(page, 'defaults', {}).get('mobileHeroImage', ''),
                'heroTitle':        getattr(page, 'defaults', {}).get('heroTitle', ''),
            },
            # categories format: [{
            #                     "desktopHeroImage":"__img_url__.png"
            #                     "displayName":"For Her",
            #                     "mobileHeroImage":"__img_url__.jpg",
            #                     "name":"for-her",
            #                   },
            #                   { ... }]
            'categories':           may_be_json(page, 'categories', list),
            'mobileCategories':     may_be_json(page, 'mobileCategories', list),
            # sticky categories can be: <bool> or <string> "desktop-only", "mobile-only"
            'stickyCategories':     getattr(page, 'stickyCategories', False),
            'home': {
                'hero':             getattr(page, 'home', {}).get('hero', None),
                'category':         getattr(page, 'home', {}).get('category', ''),
            },
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
                'wideProbability':      getattr(page, 'tiles', {}).get('wideProbability', 0.5),
            },
            'masonry': {
                'transitionDuration': getattr(page, 'masonry', {}).get('transitionDuration', '0.4s'),
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
            'offset': 0,  # TODO: find a way to eliminate this variable
        }


class PageConfigSerializer(object):
    """Generates PAGES_INFO.

    This is not a subclass of Serializer as it accepts different objects
    as input.
    """
    @staticmethod
    def to_json(request, page, feed=None, store=None, algorithm=None,
                init={}, other=None):
        """
        keys in other:
        - tile_set ('product', 'content', '')
        """

        if not store:
            store = page.store

        if not feed:
            feed = page.feed

        if not algorithm:
            algorithm = 'magic'

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
        if init:
            data['page'].update({
                # init is for loading pages with content specified in the url
                # values are specified by a view handler
                'init': {
                    'category': getattr(init, 'category', None),
                    'hero':     getattr(init, 'hero', None),
                    'preview':  getattr(init, 'preview', None),
                }
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
