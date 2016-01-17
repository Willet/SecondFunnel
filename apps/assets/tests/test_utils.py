from django.db.models.signals import post_save, m2m_changed
from django.test import TestCase
import mock
import logging

from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               ProductImage, Feed, Tile, Content
from apps.assets.signals import content_m2m_changed, content_saved, product_saved, \
                                productimage_saved, tile_m2m_changed, tile_saved
from apps.assets.utils import disable_tile_serialization_signals, enable_tile_serialization_signals, \
                              disable_tile_serialization, delay_tile_serialization, TileSerializationQueue


class SignalsTests(TestCase):
    fixtures = ['assets_models.json']

    def enable_tile_serialization_signals_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=13)
        content = Content.objects.get(pk=6)
        with mock.patch('apps.assets.signals.tile_saved') as mock_tile_saved:
            with mock.patch('apps.assets.signals.tile_m2m_changed') as mock_tile_m2m_changed:
                with mock.patch('apps.assets.signals.content_m2m_changed') as mock_content_m2m_changed:
                    # verify signals are not enabled
                    tile.save()
                    self.assertEquals(mock_tile_saved.call_count, 0)
                    tile.products.add(pro)
                    self.assertEquals(mock_tile_m2m_changed.call_count, 0)
                    content.tagged_products.add(pro)
                    self.assertEquals(mock_content_m2m_changed.call_count, 0)

                    enable_tile_serialization_signals()
                    
                    # Call counts should now increment
                    tile.save()
                    self.assertEquals(mock_tile_saved.call_count, 1)
                    # tile_m2m_changed & content_m2m_changed are both m2m_changed signal recievers
                    tile.products.add(pro)
                    self.assertEquals(mock_tile_m2m_changed.call_count, 2) # m2m_changed pre_add, post_add
                    content.tagged_products.add(pro)
                    self.assertEquals(mock_content_m2m_changed.call_count, 4) # 2x m2m_changed pre_add, post_add

    def disable_tile_serialization_signals_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=13)
        content = Content.objects.get(pk=6)
        with mock.patch('apps.assets.signals.tile_saved') as mock_tile_saved:
            with mock.patch('apps.assets.signals.tile_m2m_changed') as mock_tile_m2m_changed:
                with mock.patch('apps.assets.signals.content_m2m_changed') as mock_content_m2m_changed:
                    enable_tile_serialization_signals()
                    # verify signals work
                    tile.save()
                    self.assertEquals(mock_tile_saved.call_count, 1)
                    # tile_m2m_changed & content_m2m_changed are both m2m_changed signal recievers
                    tile.products.add(pro)
                    self.assertEquals(mock_tile_m2m_changed.call_count, 2) # m2m_changed pre_add, post_add
                    content.tagged_products.add(pro)
                    self.assertEquals(mock_content_m2m_changed.call_count, 4) # 2x m2m_changed pre_add, post_add
                    
                    disable_tile_serialization_signals()
                    # None of call counts should have incremented
                    tile.save()
                    self.assertEquals(mock_tile_saved.call_count, 1)
                    tile.products.add(pro)
                    self.assertEquals(mock_tile_m2m_changed.call_count, 4) # 2x m2m_changed pre_add, post_add
                    content.tagged_products.add(pro)
                    self.assertEquals(mock_content_m2m_changed.call_count, 4) # 2x m2m_changed pre_add, post_add


class SerializationDisabledTests(TestCase):
    fixtures = ['assets_models.json']

    def tile_saved_disable_tile_serialization_test(self):
        tile = Tile.objects.get(pk=10)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with disable_tile_serialization():
                tile.save() # triggers signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
            tile.save() # triggers signal re-enabled
            self.assertEquals(mocked_handler.call_count, 1)

    def nested_disable_tile_serialization_test(self):
        tile = Tile.objects.get(pk=10)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with disable_tile_serialization():
                with disable_tile_serialization():
                    tile.save() # triggers signal disabled
                    self.assertEquals(mocked_handler.call_count, 0)
                tile.save() # triggers signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
            tile.save() # triggers signal re-enabled
            self.assertEquals(mocked_handler.call_count, 1)

    def productimage_saved_disable_tile_serialization_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=13)
        product_image = ProductImage.objects.get(pk=11)
        tile.products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with disable_tile_serialization():
                product_image.save() # triggers signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
            product_image.save() # triggers signal re-enabled
            self.assertEquals(mocked_handler.call_count, 1)

    def product_saved_disable_tile_serialization_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with disable_tile_serialization():
                pro.save() # triggers signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
            pro.save() # triggers signal re-enabled
            self.assertEquals(mocked_handler.call_count, 1)

    def content_saved_disable_tile_serialization_test(self):
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        tile.content.add(content)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with disable_tile_serialization():
                content.save() # triggers signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
            content.save() # triggers signal re-enabled
            self.assertEquals(mocked_handler.call_count, 1)

    def content_m2m_changed_similar_products_disable_tile_serialization_test(self):
        # sufficient to demonstrate signal is disabled / re-enabled
        # all possible inputs covered by signal test
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        pro2 = Product.objects.get(pk=12)
        tile.products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with disable_tile_serialization():
                pro.similar_products.add(pro2) # triggers signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
                pro.similar_products.remove(pro2)
            pro.similar_products.add(pro2) # triggers signal re-enabled
            self.assertEquals(mocked_handler.call_count, 1)

    def content_m2m_changed_tagged_products_disable_tile_serialization_test(self):
        # sufficient to demonstrate signal is disabled / re-enabled
        # all possible inputs covered by signal test
        content = Content.objects.get(pk=6)
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.content.add(content)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with disable_tile_serialization():
                content.tagged_products.add(pro) # triggers signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
                content.tagged_products.remove(pro)
            content.tagged_products.add(pro) # triggers signal re-enabled
            self.assertEquals(mocked_handler.call_count, 1)

    def tile_m2m_changed_add_product_disable_tile_serialization_test(self):
        # sufficient to demonstrate signal is disabled / re-enabled
        # all possible inputs covered by signal test
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with disable_tile_serialization():
                tile.products.add(pro) # triggers signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
                tile.products.remove(pro)
            tile.products.add(pro) # triggers signal re-enabled
            self.assertEquals(mocked_handler.call_count, 1)

    def tile_m2m_changed_add_content_disable_tile_serialization_test(self):
        # sufficient to demonstrate signal is disabled / re-enabled
        # all possible inputs covered by signal test
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with disable_tile_serialization():
                tile.content.add(content) # trigger signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
                tile.content.remove(content)
            tile.content.add(content) # trigger signal re-enabled
            self.assertEquals(mocked_handler.call_count, 1)


class TileSerializationQueueTests(TestCase):
    fixtures = ['assets_models.json']

    def add_tile_test(self):
        tile = Tile.objects.get(pk=10)
        queue = TileSerializationQueue()
        queue.add(tile)
        self.assertEquals(len(queue), 1)

    def add_tiles_test(self):
        tile1 = Tile.objects.get(pk=10)
        tile2 = Tile.objects.get(pk=11)
        tiles = [tile1, tile2]
        queue = TileSerializationQueue()
        queue.add(tiles)
        self.assertEquals(len(queue), 2)

    def add_keyerror_test(self):
        tile1 = Tile.objects.get(pk=10)
        tiles = [tile1, 2]
        queue = TileSerializationQueue()
        with self.assertRaises(TypeError):
            queue.add(tiles)

    def start_test(self):
        tile1 = Tile.objects.get(pk=10)
        tile2 = Tile.objects.get(pk=11)
        pro = Product.objects.get(pk=13)
        content = Content.objects.get(pk=6)
        queue = TileSerializationQueue()
        with mock.patch('apps.assets.signals.tile_saved') as mock_tile_saved:
            with mock.patch('apps.assets.signals.tile_m2m_changed') as mock_tile_m2m_changed:
                with mock.patch('apps.assets.signals.content_m2m_changed') as mock_content_m2m_changed:
                    enable_tile_serialization_signals()
                    # verify signals work
                    tile1.save()
                    self.assertEquals(mock_tile_saved.call_count, 1)
                    # tile_m2m_changed & content_m2m_changed are both m2m_changed signal recievers
                    tile2.content.add(content)
                    self.assertEquals(mock_tile_m2m_changed.call_count, 2) # m2m_changed pre_add, post_add
                    content.tagged_products.add(pro)
                    self.assertEquals(mock_content_m2m_changed.call_count, 4) # 2x m2m_changed pre_add, post_add
                    
                    queue.start()
                    # None of call counts should have incremented
                    tile1.save() # queue's tile1
                    self.assertEquals(mock_tile_saved.call_count, 1)
                    tile2.products.add(pro) # queue's tile2
                    self.assertEquals(mock_tile_m2m_changed.call_count, 4)
                    content.tagged_products.add(pro) # queue's tile2 again
                    self.assertEquals(mock_content_m2m_changed.call_count, 4)
                    # queue is tile1 & tile2
                    self.assertEquals(len(queue), 2)

    def stop_test(self):
        tile1 = Tile.objects.get(pk=10)
        tile2 = Tile.objects.get(pk=11)
        pro = Product.objects.get(pk=13)
        content = Content.objects.get(pk=6)
        queue = TileSerializationQueue()
        with mock.patch('apps.assets.signals.tile_saved') as mock_tile_saved:
            with mock.patch('apps.assets.signals.tile_m2m_changed') as mock_tile_m2m_changed:
                with mock.patch('apps.assets.signals.content_m2m_changed') as mock_content_m2m_changed:
                    enable_tile_serialization_signals()
                    queue.start()

                    # verify signals disabled
                    tile1.save()
                    self.assertEquals(mock_tile_saved.call_count, 0)
                    tile2.content.add(content)
                    self.assertEquals(mock_tile_m2m_changed.call_count, 0)
                    content.tagged_products.add(pro)
                    self.assertEquals(mock_content_m2m_changed.call_count, 0)
                    self.assertEquals(len(queue), 2) # queue is tile1 & tile2

                    # reset queue
                    queue.tiles_to_serialize = set()

                    queue.stop()
                    # Signals reconnected
                    tile1.save()
                    self.assertEquals(mock_tile_saved.call_count, 1)
                    # tile_m2m_changed & content_m2m_changed are both m2m_changed signal recievers
                    tile2.products.add(pro)
                    self.assertEquals(mock_tile_m2m_changed.call_count, 2) # m2m_changed pre_add, post_add
                    content.tagged_products.add(pro)
                    self.assertEquals(mock_content_m2m_changed.call_count, 4) # 2x m2m_changed pre_add, post_add
                    # No tiles queued
                    self.assertEquals(len(queue), 0)

    def serialize_test(self):
        tile1 = Tile.objects.get(pk=10)
        tile2 = Tile.objects.get(pk=11)
        pro = Product.objects.get(pk=13)
        content = Content.objects.get(pk=6)
        queue = TileSerializationQueue()
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            queue.start()
            tile1.save()
            tile2.save()
            self.assertEquals(mocked_handler.call_count, 0)
            queue.stop()
            queue.serialize()
            self.assertEquals(mocked_handler.call_count, 2)
            self.assertEquals(len(queue), 0)

class SerializationDelayedTests(TestCase):
    fixtures = ['assets_models.json']

    def tile_saved_delay_tile_serialization_test(self):
        tile = Tile.objects.get(pk=10)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with delay_tile_serialization():
                tile.save() # triggers signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
            self.assertEquals(mocked_handler.call_count, 1)

    def nested_delay_tile_serialization_test(self):
        tile = Tile.objects.get(pk=10)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with delay_tile_serialization():
                with delay_tile_serialization():
                    tile.save() # triggers signal disabled
                    self.assertEquals(mocked_handler.call_count, 0)
                self.assertEquals(mocked_handler.call_count, 0)
            self.assertEquals(mocked_handler.call_count, 1)

    def productimage_saved_delay_tile_serialization_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=13)
        product_image = ProductImage.objects.get(pk=11)
        tile.products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with delay_tile_serialization():
                product_image.save() # triggers signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
            self.assertEquals(mocked_handler.call_count, 1)

    def product_saved_delay_tile_serialization_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with delay_tile_serialization():
                pro.save() # triggers signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
            self.assertEquals(mocked_handler.call_count, 1)

    def content_saved_delay_tile_serialization_test(self):
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        tile.content.add(content)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with delay_tile_serialization():
                content.save() # triggers signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
            self.assertEquals(mocked_handler.call_count, 1)

    def content_m2m_changed_similar_products_delay_tile_serialization_test(self):
        # sufficient to demonstrate signal is disabled / re-enabled
        # all possible inputs covered by signal test
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        pro2 = Product.objects.get(pk=12)
        tile.products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with delay_tile_serialization():
                pro.similar_products.add(pro2) # triggers signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
            self.assertEquals(mocked_handler.call_count, 1)

    def content_m2m_changed_tagged_products_delay_tile_serialization_test(self):
        # sufficient to demonstrate signal is disabled / re-enabled
        # all possible inputs covered by signal test
        content = Content.objects.get(pk=6)
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.content.add(content)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with delay_tile_serialization():
                content.tagged_products.add(pro) # triggers signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
            self.assertEquals(mocked_handler.call_count, 1)

    def tile_m2m_changed_add_product_delay_tile_serialization_test(self):
        # sufficient to demonstrate signal is disabled / re-enabled
        # all possible inputs covered by signal test
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with delay_tile_serialization():
                tile.products.add(pro) # triggers signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
                tile.products.remove(pro)
            self.assertEquals(mocked_handler.call_count, 1)

    def tile_m2m_changed_add_content_delay_tile_serialization_test(self):
        # sufficient to demonstrate signal is disabled / re-enabled
        # all possible inputs covered by signal test
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            with delay_tile_serialization():
                tile.content.add(content) # trigger signal disabled
                self.assertEquals(mocked_handler.call_count, 0)
            self.assertEquals(mocked_handler.call_count, 1)
