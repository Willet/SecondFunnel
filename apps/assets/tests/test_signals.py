from django.test import TestCase
import mock
import logging
from django.db.models.signals import post_save, m2m_changed

from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               ProductImage, Feed, Tile, Content
from apps.assets.signals import content_m2m_changed, content_saved, product_saved, \
                                productimage_saved, tile_m2m_changed, tile_saved


class SignalsTest(TestCase):
    fixtures = ['assets_models.json']

    def productimage_saved_call_test(self):
        product_image = ProductImage.objects.get(pk=4)
        with mock.patch('apps.assets.signals.productimage_saved', autospec=True) as mocked_handler:
            post_save.connect(mocked_handler, sender=ProductImage)
            product_image.save() # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    def product_saved_call_test(self):
        prod = Product.objects.get(pk=3)
        with mock.patch('apps.assets.signals.product_saved', autospec=True) as mocked_handler:
            post_save.connect(mocked_handler, sender=Product)
            prod.save() # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    def content_saved_call_test(self):
        prod = Content.objects.get(pk=6)
        with mock.patch('apps.assets.signals.content_saved', autospec=True) as mocked_handler:
            post_save.connect(mocked_handler, sender=Content)
            prod.save() # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    def content_m2m_changed_call_product_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        pro2 = Product.objects.get(pk=12)
        tile.products.add(pro)
        with mock.patch('apps.assets.signals.content_m2m_changed', autospec=True) as mocked_handler:
            m2m_changed.connect(mocked_handler, sender=Product.similar_products.through)
            pro.similar_products.add(pro2)
            specialcall = next((kwargs for args,kwargs in mocked_handler.call_args_list if kwargs["action"] == "post_add"), None)
            logging.debug(specialcall)
            self.assertEqual(specialcall['model'], Product)
            self.assertEqual(specialcall['action'], "post_add")
            self.assertEqual(specialcall['sender'], Product.similar_products.through)
            self.assertEqual(specialcall['instance'], pro)
            self.assertEqual(specialcall['pk_set'], set([pro2.pk]))

    def content_m2m_changed_call_test(self):
        content = Content.objects.get(pk=6)
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.content.add(content)
        with mock.patch('apps.assets.signals.content_m2m_changed', autospec=True) as mocked_handler:
            m2m_changed.connect(mocked_handler, sender=Content.tagged_products.through)
            content.tagged_products.add(pro)
            specialcall = next((kwargs for args,kwargs in mocked_handler.call_args_list if kwargs["action"] == "post_add"), None)
            self.assertEqual(specialcall['model'], Product)
            self.assertEqual(specialcall['action'], "post_add")
            self.assertEqual(specialcall['sender'], Content.tagged_products.through)
            self.assertEqual(specialcall['instance'], content)
            self.assertEqual(specialcall['pk_set'], set([pro.pk]))

    def tile_m2m_changed_add_product_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        with mock.patch('apps.assets.signals.tile_m2m_changed', autospec=True) as mocked_handler:
            m2m_changed.connect(mocked_handler, sender=Tile.products.through)
            tile.products.add(pro)
            specialcall = next((kwargs for args,kwargs in mocked_handler.call_args_list if kwargs["action"] == "post_add"), None)
            self.assertEqual(specialcall['model'], Product)
            self.assertEqual(specialcall['action'], "post_add")
            self.assertEqual(specialcall['sender'], Tile.products.through)
            self.assertEqual(specialcall['instance'], tile)
            self.assertEqual(specialcall['pk_set'], set([pro.pk]))

    def tile_m2m_changed_remove_product_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.products.add(pro)
        with mock.patch('apps.assets.signals.tile_m2m_changed', autospec=True) as mocked_handler:
            m2m_changed.connect(mocked_handler, sender=Tile.products.through)
            tile.products.remove(pro)
            specialcall = next((kwargs for args,kwargs in mocked_handler.call_args_list if kwargs["action"] == "post_remove"), None)
            logging.debug(specialcall)
            self.assertEqual(specialcall['model'], Product)
            self.assertEqual(specialcall['action'], "post_remove")
            self.assertEqual(specialcall['sender'], Tile.products.through)
            self.assertEqual(specialcall['instance'], tile)
            self.assertEqual(specialcall['pk_set'], set([pro.pk]))

    def tile_m2m_changed_clear_product_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.products.add(pro)
        with mock.patch('apps.assets.signals.tile_m2m_changed', autospec=True) as mocked_handler:
            m2m_changed.connect(mocked_handler, sender=Tile.products.through)
            tile.products.clear()
            specialcall = next((kwargs for args,kwargs in mocked_handler.call_args_list if kwargs["action"] == "post_clear"), None)
            logging.debug(specialcall)
            self.assertEqual(specialcall['model'], Product)
            self.assertEqual(specialcall['action'], "post_clear")
            self.assertEqual(specialcall['sender'], Tile.products.through)
            self.assertEqual(specialcall['instance'], tile)
            self.assertEqual(specialcall['pk_set'], None)

    def tile_m2m_changed_add_content_test(self):
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        with mock.patch('apps.assets.signals.tile_m2m_changed', autospec=True) as mocked_handler:
            m2m_changed.connect(mocked_handler, sender=Tile.content.through)
            tile.content.add(content)
            specialcall = next((kwargs for args,kwargs in mocked_handler.call_args_list if kwargs["action"] == "post_add"), None)
            logging.debug(specialcall)
            self.assertEqual(specialcall['model'], Content)
            self.assertEqual(specialcall['action'], "post_add")
            self.assertEqual(specialcall['sender'], Tile.content.through)
            self.assertEqual(specialcall['instance'], tile)
            self.assertEqual(specialcall['pk_set'], set([content.pk]))

    def tile_m2m_changed_remove_content_test(self):
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        tile.content.add(content)
        with mock.patch('apps.assets.signals.tile_m2m_changed', autospec=True) as mocked_handler:
            m2m_changed.connect(mocked_handler, sender=Tile.content.through)
            tile.content.remove(content) # trigger signal
            specialcall = next((kwargs for args,kwargs in mocked_handler.call_args_list if kwargs["action"] == "post_remove"), None)
            logging.debug(specialcall)
            self.assertEqual(specialcall['model'], Content)
            self.assertEqual(specialcall['action'], "post_remove")
            self.assertEqual(specialcall['sender'], Tile.content.through)
            self.assertEqual(specialcall['instance'], tile)
            self.assertEqual(specialcall['pk_set'], set([content.pk]))

    def tile_m2m_changed_clear_content_test(self):
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        tile.content.add(content)
        with mock.patch('apps.assets.signals.tile_m2m_changed', autospec=True) as mocked_handler:
            m2m_changed.connect(mocked_handler, sender=Tile.content.through)
            tile.content.clear() # trigger signal
            specialcall = next((kwargs for args,kwargs in mocked_handler.call_args_list 
                if kwargs["action"] == "post_clear"), None)
            logging.debug(specialcall)
            self.assertEqual(specialcall['model'], Content)
            self.assertEqual(specialcall['action'], "post_clear")
            self.assertEqual(specialcall['sender'], Tile.content.through)
            self.assertEqual(specialcall['instance'], tile)
            self.assertEqual(specialcall['pk_set'], None)

    def tile_saved_call_test(self):
        tile = Tile.objects.get(pk=10)
        with mock.patch('apps.assets.signals.tile_saved', autospec=True) as mocked_handler:
            post_save.connect(mocked_handler, sender=Tile)
            tile.save() # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)


class SignalExecutionTest(TestCase):
    fixtures = ['assets_models.json']

    def productimage_saved_execute_test(self):
        product_image = ProductImage.objects.get(pk=11)
        with mock.patch('apps.assets.models.Product.save', mock.Mock()) as mockery:
            productimage_saved(product_image, instance=product_image)
            self.assertEqual(mockery.call_count, 1)

    def productimage_saved_no_test(self):
        product_image = ProductImage.objects.get(pk=4)
        with mock.patch('apps.assets.models.Product.save', mock.Mock()) as mockery:
            productimage_saved(product_image, instance=product_image)
            self.assertEqual(mockery.call_count, 0)

    def product_saved_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.products.add(pro)
        with mock.patch('apps.assets.models.Tile.save', mock.Mock()) as mockery:
            product_saved(pro, instance=pro)
            self.assertEqual(mockery.call_count, 1)

    def product_saved_no_test(self):
        pro = Product.objects.get(pk=3)
        with mock.patch('apps.assets.models.Tile.save', mock.Mock()) as mockery:
            product_saved(pro, instance=pro)
            self.assertEqual(mockery.call_count, 0)

    def content_saved_test(self):
        tile = Tile.objects.get(pk=10)
        con = Content.objects.get(pk=6)
        tile.content.add(con)
        with mock.patch('apps.assets.models.Tile.save', mock.Mock()) as mockery:
            content_saved(con, instance=con)
            self.assertEqual(mockery.call_count, 1)

    def content_saved_no_test(self):
        con = Content.objects.get(pk=6)
        with mock.patch('apps.assets.models.Tile.save', mock.Mock()) as mockery:
            content_saved(con, instance=con)
            self.assertEqual(mockery.call_count, 0)

    def content_m2m_changed_test(self):
        con = Content.objects.get(pk=6)
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.content.add(con)
        con.tagged_products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mockery:
            content_m2m_changed(Content.tagged_products.through, instance=con, pk_set=[pro.pk], action="post_add")
            self.assertEqual(mockery.call_count, 1)

    def content_m2m_changed_no_test(self):
        con = Content.objects.get(pk=6)
        pro = Product.objects.get(pk=3)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock()) as mockery:
            content_m2m_changed(Content.tagged_products.through, instance=con, pk_set=[pro.pk], action="post_add")
            self.assertEqual(mockery.call_count, 0)

    def content_m2m_changed_product_test(self):
        con = Content.objects.get(pk=6)
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        pro2 = Product.objects.get(pk=12)
        tile.products.add(pro)
        pro.similar_products.add(pro2) # signal trigger
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mockery:
            content_m2m_changed(Product.similar_products.through, instance=pro, pk_set=[pro2.pk], action="post_add")
            self.assertEqual(mockery.call_count, 1)

    def content_m2m_changed_product_no_test(self):
        con = Content.objects.get(pk=6)
        pro = Product.objects.get(pk=3)
        pro2 = Product.objects.get(pk=12)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock()) as mockery:
            content_m2m_changed(Product.similar_products.through, instance=pro, pk_set=[], action="post_add")
            self.assertEqual(mockery.call_count, 0)

    def content_m2m_changed_product_no_test(self):
        con = Content.objects.get(pk=6)
        pro = Product.objects.get(pk=3)
        pro2 = Product.objects.get(pk=12)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock()) as mockery:
            content_m2m_changed(Product.similar_products.through, instance=pro, pk_set=[], action="post_add")
            self.assertEqual(mockery.call_count, 0)

    def tile_m2m_changed_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mockery:
            tile_m2m_changed(Tile.products.through, model=Product, instance=tile, pk_set=[pro.pk], action="post_add")
            self.assertEqual(mockery.call_count, 1)

    def tile_m2m_changed_remove_product_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.products.add(pro)
        tile.products.remove(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mockery:
            tile_m2m_changed(Tile.products.through, model=Product, instance=tile, pk_set=[pro.pk], action="post_remove")
            self.assertEqual(mockery.call_count, 1)

    def tile_m2m_changed_clear_product_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.products.add(pro)
        tile.products.clear()
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock()) as mockery:
            tile_m2m_changed(Tile.products.through, model=Product, instance=tile, action="post_clear")
            self.assertEqual(mockery.call_count, 0) # no tiles no call

    def tile_m2m_changed_add_content_test(self):
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        tile.content.add(content)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mockery:
            tile_m2m_changed(Tile.content.through, instance=tile, pk_set=[content.pk], action="post_add")
            self.assertEqual(mockery.call_count, 1)

    def tile_m2m_changed_remove_content_test(self):
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        tile.content.add(content)
        tile.content.remove(content) # trigger signal
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mockery:
            tile_m2m_changed(Tile.content.through, instance=tile, pk_set=[content.pk], action="post_remove")
            self.assertEqual(mockery.call_count, 1)

    def tile_m2m_changed_clear_content_test(self):
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        tile.content.add(content)
        tile.content.clear() # trigger signal
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock()) as mockery:
            tile_m2m_changed(Tile.content.through, instance=tile, action="post_clear")
            self.assertEqual(mockery.call_count, 0) # no tiles no call

    def tile_saved_test(self):
        tile = Tile.objects.get(pk=10)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mockery:
            tile_saved(tile, instance=tile)
            self.assertEqual(mockery.call_count, 1)


class SerializationSignalTests(TestCase):
    fixtures = ['assets_models.json']

    def productimage_saved_trigger_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=13)
        product_image = ProductImage.objects.get(pk=11)
        tile.products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            product_image.save() # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    def product_saved_trigger_test(self):
        tile = Tile.objects.get(pk=10)
        prod = Product.objects.get(pk=3)
        tile.products.add(prod)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            prod.save() # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    def content_saved_trigger_test(self):
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        tile.content.add(content)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            content.save() # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    # product.similar_products add, remove, clear
    def content_m2m_changed_add_similar_product_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        pro2 = Product.objects.get(pk=12)
        tile.products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            pro.similar_products.add(pro2) # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    def content_m2m_changed_remove_similar_product_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        pro2 = Product.objects.get(pk=12)
        tile.products.add(pro)
        pro.similar_products.add(pro2)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            pro.similar_products.remove(pro2) # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    def content_m2m_changed_clear_similar_product_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        pro2 = Product.objects.get(pk=12)
        tile.products.add(pro)
        pro.similar_products.add(pro2)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            pro.similar_products.clear() # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    #  product.reverse_similar_products (reverse of product.similar_products) add, remove, clear
    def content_m2m_changed_add_similar_product_through_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        pro2 = Product.objects.get(pk=12)
        tile.products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            pro2.reverse_similar_products.add(pro) # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    def content_m2m_changed_remove_similar_product_through_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        pro2 = Product.objects.get(pk=12)
        tile.products.add(pro)
        pro.similar_products.add(pro2)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            pro2.reverse_similar_products.remove(pro) # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    def content_m2m_changed_clear_similar_product_through_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        pro2 = Product.objects.get(pk=12)
        tile.products.add(pro)
        pro.similar_products.add(pro2)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            pro2.reverse_similar_products.clear() # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    # content.tagged_products add, remove, clear
    def content_m2m_changed_add_tagged_product_test(self):
        content = Content.objects.get(pk=6)
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.content.add(content)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            content.tagged_products.add(pro)
            self.assertEquals(mocked_handler.call_count, 1)

    def content_m2m_changed_remove_tagged_product_test(self):
        content = Content.objects.get(pk=6)
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.content.add(content)
        content.tagged_products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            content.tagged_products.remove(pro) # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    def content_m2m_changed_clear_tagged_product_test(self):
        content = Content.objects.get(pk=6)
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.content.add(content)
        content.tagged_products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            content.tagged_products.clear() # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    # product.content (reverse of content.tagged_products) add, remove, clear
    def content_m2m_changed_add_tagged_product_through_test(self):
        content = Content.objects.get(pk=6)
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.content.add(content)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            pro.content.add(content) # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    def content_m2m_changed_remove_tagged_product_through_test(self):
        content = Content.objects.get(pk=6)
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.content.add(content)
        content.tagged_products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            pro.content.remove(content) # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    def content_m2m_changed_clear_tagged_product_through_test(self):
        content = Content.objects.get(pk=6)
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.content.add(content)
        content.tagged_products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            pro.content.clear() # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    # tile.products add, remove, clear
    def tile_m2m_changed_add_product_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            tile.products.add(pro)
            self.assertEquals(mocked_handler.call_count, 1)

    def tile_m2m_changed_remove_product_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            tile.products.remove(pro)
            self.assertEquals(mocked_handler.call_count, 1)

    def tile_m2m_changed_clear_product_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            tile.products.clear()
            self.assertEquals(mocked_handler.call_count, 0)

    # product.tiles (reverse of tile.products) add, remove, clear
    def tile_m2m_changed_add_product_through_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            pro.tiles.add(tile)
            self.assertEquals(mocked_handler.call_count, 1)

    def tile_m2m_changed_remove_product_through_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            pro.tiles.remove(tile)
            self.assertEquals(mocked_handler.call_count, 1)

    def tile_m2m_changed_clear_product_through_test(self):
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            pro.tiles.clear()
            self.assertEquals(mocked_handler.call_count, 0)

    # tile.content add, remove, clear
    def tile_m2m_changed_add_content_test(self):
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            tile.content.add(content)
            self.assertEquals(mocked_handler.call_count, 1)

    def tile_m2m_changed_remove_content_test(self):
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        tile.content.add(content)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            tile.content.remove(content) # trigger signal
            self.assertEquals(mocked_handler.call_count, 1)

    def tile_m2m_changed_clear_content_test(self):
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        tile.content.add(content)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            tile.content.clear() # trigger signal
            self.assertEquals(mocked_handler.call_count, 1)

    # content.tiles (reverse of tile.content) add, remove, clear
    def tile_m2m_changed_add_content_through_test(self):
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            content.tiles.add(tile)
            self.assertEquals(mocked_handler.call_count, 1)

    def tile_m2m_changed_remove_content_through_test(self):
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        tile.content.add(content)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            content.tiles.remove(tile) # trigger signal
            self.assertEquals(mocked_handler.call_count, 1)

    def tile_m2m_changed_clear_content_through_test(self):
        tile = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        tile.content.add(content)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=('', False))) as mocked_handler:
            content.tiles.clear() # trigger signal
            self.assertEquals(mocked_handler.call_count, 1)
