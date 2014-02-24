"""
To import store, products, content, tiles, and themes from store 38, type:
$ ./manage.py importer 38
"""
from apps.assets.models import (Store, Image, Video, Product, ProductImage,
                                Theme, Page, Feed, Tile)
from apps.contentgraph.models import get_contentgraph_data, call_contentgraph
from django.core.management.base import BaseCommand, CommandError


products = {}
contents = {}


def update_or_create(model, defaults=None, **kwargs):
    """
    tries to find and then update model
    if the find fails, it creates a new model (sic)
    """
    prop_bag = defaults
    prop_bag.update(kwargs)
    obj, created = model.objects.get_or_create(defaults=prop_bag, **kwargs)
    if not created:
        for field in prop_bag:
            setattr(obj, field, prop_bag[field])
        obj.save()
    return obj


class Command(BaseCommand):
    """WARNING: this script can only import ONE store at a time."""
    store = None
    store_id = 0

    def handle(self, *args, **kwargs):
        self.store_id = args[0]
        if not self.store_id:
            raise CommandError("Not a valid store id for argument 0")

        self.import_store()
        if len(args) == 1:  # only store id supplied
            self.import_products()
            self.import_content()
            self.import_pages()
        else:
            if 'products' in args:
                self.import_products()
            if 'content' in args:
                self.import_content()
            if 'pages' in args:
                self.import_pages()

    def _store_url(self, store_id=None):
        """returns CG url for a store, or if no store, then all stores."""
        store_id = store_id or self.store_id
        if store_id:
            return 'store/{0}/'.format(store_id)
        else:
            return 'store/'

    def import_store(self, store_id=0):
        store = call_contentgraph(self._store_url(store_id=store_id))
        store_old_id = store.get('id')
        store_name = store.get('name')
        store_slug = store.get('slug')
        store_description = store.get('description')
        store_public_base_url = store.get('public-base-url')

        store_fields = {'name': store_name, 'slug': store_slug,
                        'description': store_description,
                        'public_base_url': store_public_base_url}

        print 'STORE - old_id: ', store_old_id, ', ', store_fields

        self.store = update_or_create(Store, old_id=store_old_id,
                                      defaults=store_fields)


    def import_products(self, store_id=0):
        for product in get_contentgraph_data(self._store_url(store_id=store_id) + 'product/'):
            product_old_id = product.get('id')
            product_name = product.get('name')
            product_description = product.get('description')
            product_url = product.get('url')
            product_sku = product.get('sku')
            product_price = product.get('price')

            product_default_image_old_id = product.get('default-image-id')
            if not product_default_image_old_id:
                continue

            product_fields = {'store': self.store, 'name': product_name,
                              'description': product_description,
                              'url': product_url, 'sku': product_sku,
                              'price': product_price}

            print 'PRODUCT - old_id: ', product_old_id, ', ', product_fields

            #the product must be created before the images as the product-images require a product
            product_psql = update_or_create(Product, old_id=product_old_id,
                                            defaults=product_fields)

            product_image_old_ids = product.get('image-ids')
            if product_default_image_old_id not in product_image_old_ids:
                product_image_old_ids.append(product_default_image_old_id)

            product_image_fields = {'product': product_psql}

            for product_image_old_id in product_image_old_ids:
                for product_image in get_contentgraph_data(
                                        self._store_url(store_id=store_id) + 'content/' + product_image_old_id):
                    product_image_url = product_image.get('url')
                    product_image_original_url = product_image.get(
                        'original-url')

                    product_image_fields.update({'url': product_image_url,
                                                 'original_url': product_image_original_url})

                    print 'PRODUCT IMAGE - old_id: ', product_image_old_id, ', ', product_image_fields

                    update_or_create(ProductImage, old_id=product_image_old_id,
                                     defaults=product_image_fields)

            product_image_psql = ProductImage.objects.get(
                old_id=product_default_image_old_id)

            # setting the default product-image on the product
            product_psql.default_image_id = product_image_psql.id
            product_psql.save()
            products[product_old_id] = product_psql.id


    def import_content(self, store_id=0):
        for content in get_contentgraph_data(self._store_url(store_id=store_id) + 'content/'):
            content_old_id = content.get('id')
            content_source = content.get('source')
            # if the image has source 'image' (product image), skip
            if content_source == 'image':
                continue
            content_type = content.get('type')
            content_products_object = content.get('tagged-products')
            content_tagged_products = ''
            if content_products_object:
                for product_id in content_products_object:
                    if len(content_tagged_products) > 0:
                        content_tagged_products += ',' + str(
                            products.get(str(product_id)))
                    else:
                        content_tagged_products += str(
                            products.get(str(product_id)))

            content_name = content.get('name')
            content_description = content.get('description')

            content_fields = {'store': self.store, 'source': content_source,
                              'tagged_products': content_tagged_products,
                              'name': content_name,
                              'description': content_description}

            if content_type == 'image':
                content_url = content.get('url')
                content_original_url = content.get('original-url')
                content_source_url = content.get('source-url')

                content_fields.update(
                    {'url': content_url, 'original_url': content_original_url,
                     'source_url': content_source_url})

                print 'IMAGE - old_id: ', content_old_id, ', ', content_fields

                content_psql = update_or_create(Image, old_id=content_old_id,
                                                defaults=content_fields)
            elif content_type == 'video':
                content_url = content.get('original-url')
                content_source_url = content_url

                content_fields.update(
                    {'url': content_url, 'source_url': content_source_url})

                print 'VIDEO - old_id: ', content_old_id, ', ', content_fields

                content_psql = update_or_create(Video, old_id=content_old_id,
                                                defaults=content_fields)

            else:
                continue
            contents[content_old_id] = content_psql.id


    def import_pages(self, store_id=0):
        for page in get_contentgraph_data(self._store_url(store_id=store_id) + 'page/'):
            page_old_id = page.get('id')
            if not page_old_id in ['91', '95', '98']:
                continue
            page_name = page.get('name')
            page_legal_copy = page.get('legalCopy')
            page_url_slug = page.get('url')
            page_theme_template = page.get('theme')

            # since feeds have no fields except id right now, the only way to find the feed is based on the page's feed_id
            try:
                page_psql = Page.objects.get(old_id=page_old_id)
                feed_psql = Feed.objects.get(id=page_psql.feed_id)
            except Page.DoesNotExist:
                feed_psql = Feed()
                feed_psql.save()

            page_theme_fields = {}

            print 'THEME - template: ', page_theme_template, ', ', page_theme_fields

            theme_psql = update_or_create(Theme, template=page_theme_template,
                                          defaults=page_theme_fields)

            page_fields = {'feed': feed_psql, 'theme': theme_psql,
                           'name': page_name, 'legal_copy': page_legal_copy,
                           'url_slug': page_url_slug}

            print 'PAGE - old_id: ', page_old_id, ', ', page_fields

            update_or_create(Page, old_id=page_old_id, defaults=page_fields)
            self.import_tiles(page_old_id, feed_psql)


    def import_tiles(self, page_id, feed_psql):
        for tile in get_contentgraph_data('page/' + str(page_id) + '/tile/'):
            tile_old_id = tile.get('id')
            tile_template = tile.get('template')
            tile_prioritized = tile.get('prioritized') in ['true', 'True']

            tile_fields = {'feed': feed_psql, 'template': tile_template,
                           'prioritized': tile_prioritized}

            print 'TILE - old_id: ', tile_old_id, ', ', tile_fields

            tile_psql = update_or_create(Tile, old_id=tile_old_id,
                                         defaults=tile_fields)
            tile_content_old_ids = tile.get('content-ids')
            if tile_content_old_ids:
                for content_old_id in tile_content_old_ids:
                    if contents.get(str(content_old_id)):
                        tile_psql.content.add(contents[str(content_old_id)])
            tile_product_old_ids = tile.get('product-ids')
            if tile_product_old_ids:
                for product_old_id in tile_product_old_ids:
                    if products.get(str(product_old_id)):
                        tile_psql.products.add(products[str(product_old_id)])

