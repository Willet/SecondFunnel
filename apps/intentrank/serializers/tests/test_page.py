from django.test import TestCase
import mock
import logging
from datetime import datetime
from django.conf import settings

from apps.utils.functional import may_be_json
from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               ProductImage, Feed, Tile, Content
import apps.intentrank.serializers as ir_serializers
from apps.intentrank.serializers.utils import SerializerError

class FeedSerializerTest(TestCase):
    fixtures = ['assets_models.json']

    def get_dump_object_test(self):
        s = ir_serializers.FeedSerializer()
        feed = Feed.objects.get(pk=9)
        data = s.get_dump_object(feed)
        self.assertEqual(data['id'], str(feed.id))
        self.assertEqual(data['algorithm'], feed.feed_algorithm)

class StoreSerializerTest(TestCase):
    fixtures = ['assets_models.json']

    def get_dump_object_test(self):
        s = ir_serializers.StoreSerializer()
        store = Store.objects.get(pk=1)
        data = s.get_dump_object(store)
        self.assertEqual(data['id'], str(store.id))
        self.assertEqual(data['slug'], store.slug or "store")
        self.assertEqual(data['name'], store.name or "Store")
        self.assertEqual(data['displayName'], getattr(store, 'display_name', ''))
        self.assertIsNone(data['defaultPageName']) # no default page

    def get_dump_object_test(self):
        s = ir_serializers.StoreSerializer()
        store = Store.objects.get(pk=1)
        page = Page.objects.get(pk=8)
        store.default_page = page
        data = s.get_dump_object(store)
        self.assertEqual(data['id'], str(store.id))
        self.assertEqual(data['slug'], store.slug or "store")
        self.assertEqual(data['name'], store.name or "Store")
        self.assertEqual(data['displayName'], getattr(store, 'display_name', ''))
        self.assertEqual(data['defaultPageName'], page.url_slug)

class PageSerializerTest(TestCase):
    fixtures = ['assets_models.json']

    def get_dump_object_test(self):
        s = ir_serializers.PageSerializer()
        page = Page.objects.get(pk=8)
        data = s.get_dump_object(page)
        self.assertEqual(data['id'], getattr(page, 'intentrank_id', page.id))
        self.assertEqual(data['name'], getattr(page, 'name', ''))
        self.assertEqual(data['slug'], getattr(page, 'url_slug', ''))
        self.assertEqual(data['layout'], getattr(page, 'layout', 'hero'))
        self.assertEqual(data['description'], getattr(page, 'description', ''))
        self.assertEqual(data['gaAccountNumber'], getattr(page, 'gaAccountNumber', settings.GOOGLE_ANALYTICS_PROPERTY))
        self.assertEqual(data['categories'], may_be_json(page, 'categories', list))
        self.assertEqual(data['mobileCategories'], may_be_json(page, 'mobileCategories', list))
        self.assertEqual(data['stickyCategories'], getattr(page, 'stickyCategories', False))
        self.assertEqual(data['showSharingCount'], getattr(page, 'showSharingCount', False))
        self.assertEqual(data['openLinksInNewWindow'], getattr(page, 'openLinksInNewWindow', True))
        self.assertEqual(data['urlParams'], getattr(page, 'urlParams', {}))
        masonry = {
            'transitionDuration': getattr(page, 'masonry', {}).get('transitionDuration', '0.4s'),
            'forceGrid':          getattr(page, 'masonry', {}).get('forceGrid', True),
            'tileAspectRatio':    getattr(page, 'masonry', {}).get('tileAspectRatio', 0.7),
            'heightRange':        getattr(page, 'masonry', {}).get('heightRange', 0.6),
        }
        self.assertEqual(data['masonry'], masonry)
        tiles = {
            'openTileInHero':       getattr(page, 'tiles', {}).get('openTileInHero', False),
            'openProductTileInPDP': getattr(page, 'tiles', {}).get('openProductTileInPDP', False),
            'wideableTemplates':    getattr(page, 'tiles', {}).get('wideableTemplates', None),
            'wideProbability':      getattr(page, 'tiles', {}).get('wideProbability', 0.5),
        }
        self.assertEqual(data['tiles'], tiles)
        home = {
            'hero':             getattr(page, 'home', {}).get('hero', None),
            'category':         getattr(page, 'home', {}).get('category', ''),
        }
        self.assertEqual(data['home'], home)
        defaults = {
            'heroImage':        getattr(page, 'defaults', {}).get('heroImage', ''),
            'mobileHeroImage':  getattr(page, 'defaults', {}).get('mobileHeroImage', ''),
            'heroTitle':        getattr(page, 'defaults', {}).get('heroTitle', ''),
        }
        self.assertEqual(data['defaults'], defaults)

class IntentRankSerializerTest(TestCase):
    fixtures = ['assets_models.json']

    def to_json_test(self):
        s = ir_serializers.IntentRankSerializer()
        data = s.to_json()
        self.assertEqual(data['results'], 10)
        self.assertEqual(data['offset'], 0)

class PageConfigSerializerclassTest(TestCase):
    fixtures = ['assets_models.json']

    def to_json_test(self):
        s = ir_serializers.PageConfigSerializer()
        page = Page.objects.get(pk=8)
        feed = Feed.objects.get(pk=9)
        data = s.to_json(None, page, feed)
