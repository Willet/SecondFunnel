from django.test import TestCase
import mock
import logging
from django.db.models.signals import post_save, m2m_changed

from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               ProductImage, Feed, Tile, Content

from apps.assets.signals import content_m2m_changed, content_saved, product_saved, \
                                productimage_saved, tile_m2m_changed, tile_saved

# mock class
# class LocalDjangoSignalsMock():
#     def __init__(self, to_mock):
#         """ 
#         Replaces registered django signals with MagicMocks

#         :param to_mock: list of signal handlers to mock
#         """
#         self.mocks = {handler:mock.MagicMock() for handler in to_mock}
#         self.reverse_mocks = {magicmock:mocked
#                               for mocked,magicmock in self.mocks.items()}
#         django_signals = [post_save, m2m_changed]
#         self.registered_receivers = [signal.receivers
#                                      for signal in django_signals]

#     def _apply_mocks(self):
#         for receivers in self.registered_receivers:
#             for receiver_index in xrange(len(receivers)):
#                 handler = receivers[receiver_index]
#                 handler_function = handler[1]()
#                 if handler_function in self.mocks:
#                     receivers[receiver_index] = (
#                         handler[0], self.mocks[handler_function])

#     def _reverse_mocks(self):
#         for receivers in self.registered_receivers:
#             for receiver_index in xrange(len(receivers)):
#                 handler = receivers[receiver_index]
#                 handler_function = handler[1]
#                 if not isinstance(handler_function, mock.MagicMock):
#                     continue
#                 receivers[receiver_index] = (
#                     handler[0], weakref.ref(self.reverse_mocks[handler_function]))

#     def __enter__(self):
#         self._apply_mocks()
#         return self.mocks

class SignalsTest(TestCase):
    fixtures = ['assets_models.json']

    # @mock.patch('apps.assets.signals.tile_saved', mock.Mock())
    # def save_signal_test(self):
    #     t = Tile.objects.get(pk=10)
    #     # pagse
    #     to_mock = [post_save]
    #     with LocalDjangoSignalsMock(to_mock) as mocks:
    #         t.save()
    #         for mocked in to_mock:
    #             assert(mocks[mocked].call_count)

    def productimage_saved_call_test(self):
        product_image = ProductImage.objects.get(pk=4)
        with mock.patch('apps.assets.signals.productimage_saved', autospec=True) as mocked_handler:
            post_save.connect(mocked_handler, sender=ProductImage)
            product_image.save() # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    def product_saved_call_test(self):
        fix = Product.objects.get(pk=3)
        with mock.patch('apps.assets.signals.product_saved', autospec=True) as mocked_handler:
            post_save.connect(mocked_handler, sender=Product)
            fix.save() # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    def content_saved_call_test(self):
        fix = Content.objects.get(pk=6)
        with mock.patch('apps.assets.signals.content_saved', autospec=True) as mocked_handler:
            post_save.connect(mocked_handler, sender=Content)
            fix.save() # triggers signal
            self.assertEquals(mocked_handler.call_count, 1)

    def content_m2m_changed_call_product_test(self):
        fix = Content.objects.get(pk=6)
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
        fix = Content.objects.get(pk=6)
        tile = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        tile.content.add(fix)
        with mock.patch('apps.assets.signals.content_m2m_changed', autospec=True) as mocked_handler:
            m2m_changed.connect(mocked_handler, sender=Content.tagged_products.through)
            fix.tagged_products.add(pro)
            specialcall = next((kwargs for args,kwargs in mocked_handler.call_args_list if kwargs["action"] == "post_add"), None)
            logging.debug(specialcall)
            self.assertEqual(specialcall['model'], Product)
            self.assertEqual(specialcall['action'], "post_add")
            self.assertEqual(specialcall['sender'], Content.tagged_products.through)
            self.assertEqual(specialcall['instance'], fix)
            self.assertEqual(specialcall['pk_set'], set([pro.pk]))

    def tile_m2m_changed_add_product_test(self):
        fix = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        with mock.patch('apps.assets.signals.tile_m2m_changed', autospec=True) as mocked_handler:
            m2m_changed.connect(mocked_handler, sender=Tile.products.through)
            fix.products.add(pro)
            # logging.debug(mocked_handler.call_args_list)
            # args, kwargs = mocked_handler.call_args_list[1]
            specialcall = next((kwargs for args,kwargs in mocked_handler.call_args_list if kwargs["action"] == "post_add"), None)
            # call(reverse=False, signal=<django.dispatch.dispatcher.Signal object at 0x7fd13b05ed10>, instance=<Tile: Tile #10>, pk_set=set([3]), using='default', model=<class 'apps.assets.models.Product'>, action='post_add', sender=<class 'apps.assets.models.Tile_products'>)
            logging.debug(specialcall)
            self.assertEqual(specialcall['model'], Product)
            self.assertEqual(specialcall['action'], "post_add")
            self.assertEqual(specialcall['sender'], Tile.products.through)
            self.assertEqual(specialcall['instance'], fix)
            self.assertEqual(specialcall['pk_set'], set([pro.pk]))

    def tile_m2m_changed_remove_product_test(self):
        fix = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        fix.products.add(pro)
        with mock.patch('apps.assets.signals.tile_m2m_changed', autospec=True) as mocked_handler:
            m2m_changed.connect(mocked_handler, sender=Tile.products.through)
            fix.products.remove(pro)
            specialcall = next((kwargs for args,kwargs in mocked_handler.call_args_list if kwargs["action"] == "post_remove"), None)
            logging.debug(specialcall)
            self.assertEqual(specialcall['model'], Product)
            self.assertEqual(specialcall['action'], "post_remove")
            self.assertEqual(specialcall['sender'], Tile.products.through)
            self.assertEqual(specialcall['instance'], fix)
            self.assertEqual(specialcall['pk_set'], set([pro.pk]))

    def tile_m2m_changed_clear_product_test(self):
        fix = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        fix.products.add(pro)
        with mock.patch('apps.assets.signals.tile_m2m_changed', autospec=True) as mocked_handler:
            m2m_changed.connect(mocked_handler, sender=Tile.products.through)
            fix.products.clear()
            specialcall = next((kwargs for args,kwargs in mocked_handler.call_args_list if kwargs["action"] == "post_clear"), None)
            logging.debug(specialcall)
            self.assertEqual(specialcall['model'], Product)
            self.assertEqual(specialcall['action'], "post_clear")
            self.assertEqual(specialcall['sender'], Tile.products.through)
            self.assertEqual(specialcall['instance'], fix)
            self.assertEqual(specialcall['pk_set'], None)

    def tile_m2m_changed_add_content_test(self):
        fix = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        with mock.patch('apps.assets.signals.tile_m2m_changed', autospec=True) as mocked_handler:
            m2m_changed.connect(mocked_handler, sender=Tile.content.through)
            fix.content.add(content)
            specialcall = next((kwargs for args,kwargs in mocked_handler.call_args_list if kwargs["action"] == "post_add"), None)
            logging.debug(specialcall)
            self.assertEqual(specialcall['model'], Content)
            self.assertEqual(specialcall['action'], "post_add")
            self.assertEqual(specialcall['sender'], Tile.content.through)
            self.assertEqual(specialcall['instance'], fix)
            self.assertEqual(specialcall['pk_set'], set([content.pk]))

    def tile_m2m_changed_remove_content_test(self):
        fix = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        fix.content.add(content)
        with mock.patch('apps.assets.signals.tile_m2m_changed', autospec=True) as mocked_handler:
            m2m_changed.connect(mocked_handler, sender=Tile.content.through)
            fix.content.remove(content) # trigger signal
            specialcall = next((kwargs for args,kwargs in mocked_handler.call_args_list if kwargs["action"] == "post_remove"), None)
            logging.debug(specialcall)
            self.assertEqual(specialcall['model'], Content)
            self.assertEqual(specialcall['action'], "post_remove")
            self.assertEqual(specialcall['sender'], Tile.content.through)
            self.assertEqual(specialcall['instance'], fix)
            self.assertEqual(specialcall['pk_set'], set([content.pk]))

    def tile_m2m_changed_clear_content_test(self):
        fix = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        fix.content.add(content)
        with mock.patch('apps.assets.signals.tile_m2m_changed', autospec=True) as mocked_handler:
            m2m_changed.connect(mocked_handler, sender=Tile.content.through)
            fix.content.clear() # trigger signal
            specialcall = next((kwargs for args,kwargs in mocked_handler.call_args_list 
                if kwargs["action"] == "post_clear"), None)
            logging.debug(specialcall)
            self.assertEqual(specialcall['model'], Content)
            self.assertEqual(specialcall['action'], "post_clear")
            self.assertEqual(specialcall['sender'], Tile.content.through)
            self.assertEqual(specialcall['instance'], fix)
            self.assertEqual(specialcall['pk_set'], None)

    def tile_saved_call_test(self):
        fix = Tile.objects.get(pk=10)
        with mock.patch('apps.assets.signals.tile_saved', autospec=True) as mocked_handler:
            post_save.connect(mocked_handler, sender=Tile)
            fix.save() # triggers signal
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
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=(None, None))) as mockery:
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
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=(None, None))) as mockery:
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
        fix = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        fix.products.add(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock()) as mockery:
            content_m2m_changed(Tile.products.through, model=Product, instance=fix, pk_set=[pro.pk], action="post_add")
            self.assertEqual(mockery.call_count, 1)

    def tile_m2m_changed_remove_product_test(self):
        fix = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        fix.products.add(pro)
        fix.products.remove(pro)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock()) as mockery:
            content_m2m_changed(Tile.products.through, model=Product, instance=fix, pk_set=[pro.pk], action="post_remove")
            self.assertEqual(mockery.call_count, 1)
            # self.assertEqual(specialcall['model'], Product)
            # self.assertEqual(specialcall['action'], "post_remove")
            # self.assertEqual(specialcall['sender'], Tile.products.through)
            # self.assertEqual(specialcall['instance'], fix)
            # self.assertEqual(specialcall['pk_set'], set([pro.pk]))

    def tile_m2m_changed_clear_product_test(self):
        fix = Tile.objects.get(pk=10)
        pro = Product.objects.get(pk=3)
        fix.products.add(pro)
        fix.products.clear()
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock()) as mockery:
            content_m2m_changed(Tile.products.through, model=Product, instance=fix, action="post_clear")
            self.assertEqual(mockery.call_count, 1)
            # self.assertEqual(specialcall['model'], Product)
            # self.assertEqual(specialcall['action'], "post_clear")
            # self.assertEqual(specialcall['sender'], Tile.products.through)
            # self.assertEqual(specialcall['instance'], fix)
            # self.assertEqual(specialcall['pk_set'], None)

    def tile_m2m_changed_add_content_test(self):
        fix = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        fix.content.add(content)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock()) as mockery:
            content_m2m_changed(Tile.content.through, instance=fix, pk_set=[content.pk], action="post_add")
            self.assertEqual(mockery.call_count, 1)
            # self.assertEqual(specialcall['model'], Content)
            # self.assertEqual(specialcall['action'], "post_add")
            # self.assertEqual(specialcall['sender'], Tile.content.through)
            # self.assertEqual(specialcall['instance'], fix)
            # self.assertEqual(specialcall['pk_set'], set([content.pk]))

    def tile_m2m_changed_remove_content_test(self):
        fix = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        fix.content.add(content)
        fix.content.remove(content) # trigger signal
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock()) as mockery:
            content_m2m_changed(Tile.content.through, instance=fix, pk_set=[content.pk], action="post_remove")
            self.assertEqual(mockery.call_count, 1)
            # self.assertEqual(specialcall['model'], Content)
            # self.assertEqual(specialcall['action'], "post_remove")
            # self.assertEqual(specialcall['sender'], Tile.content.through)
            # self.assertEqual(specialcall['instance'], fix)
            # self.assertEqual(specialcall['pk_set'], set([content.pk]))

    def tile_m2m_changed_clear_content_test(self):
        fix = Tile.objects.get(pk=10)
        content = Content.objects.get(pk=6)
        fix.content.add(content)
        fix.content.clear() # trigger signal
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock()) as mockery:
            content_m2m_changed(Tile.content.through, instance=fix, action="post_clear")
            self.assertEqual(mockery.call_count, 1)
            # self.assertEqual(specialcall['model'], Content)
            # self.assertEqual(specialcall['action'], "post_clear")
            # self.assertEqual(specialcall['sender'], Tile.content.through)
            # self.assertEqual(specialcall['instance'], fix)
            # self.assertEqual(specialcall['pk_set'], None)

    def tile_saved_test(self):
        fix = Tile.objects.get(pk=10)
        with mock.patch('apps.assets.models.Tile.update_ir_cache', mock.Mock(return_value=(None, None))) as mockery:
            tile_saved(fix, instance=fix)
            self.assertEqual(mockery.call_count, 1)


