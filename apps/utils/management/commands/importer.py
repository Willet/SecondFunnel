"""
To import store, products, content, tiles, and themes from store 38, type:
$ ./manage.py importer 38 true
"""
import urllib
import cStringIO
import json

from PIL import Image as Img

from apps.assets.models import (Store, Image, Video, Product, ProductImage,
                                Theme, Page, Feed, Tile)
from apps.contentgraph.models import get_contentgraph_data, call_contentgraph
from django.core.management.base import BaseCommand, CommandError


products = {}
contents = {}


def get_image_sizes(image, download=True):
    if not image.get('image-sizes'):
        return {}, None, None
    image_sizes = json.loads(image.get('image-sizes'))
    if not (download or image.get('image-sizes')):
        return {'sizes': image_sizes}, None, None
    url = image.get('url')
    image_file = cStringIO.StringIO(urllib.urlopen(url).read())
    try:
        im = Img.open(image_file)
        width, height = im.size
        image_sizes['master'] = {'width': width, 'height': height}
        return {'sizes': image_sizes}, width, height
    except IOError:
        return {'sizes': image_sizes}, None, None


class Command(BaseCommand):
    """WARNING: this script can only import ONE store at a time."""
    store = None
    store_id = 0
    download_images = False

    def handle(self, *args, **kwargs):
        self.store_id = args[0]
        if len(args) > 1 and args[1] and args[1] in ['true', 'True', 't']:
            self.download_images = True
        else:
            self.download_images = False

        if not self.store_id:
            raise CommandError("Not a valid store id for argument 0")

        self.import_store(self.store_id)
        if any(s in args for s in ['products', 'content', 'pages']):
            if 'products' in args:
                self.import_products(self.store_id)
            if 'content' in args:
                self.import_content(self.store_id)
            if 'pages' in args:
                self.import_pages(self.store_id)
        else:  # only store id and download images supplied
            self.import_products(self.store_id)
            self.import_content(self.store_id)
            self.import_pages(self.store_id)


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

        self.store, _, _ = Store.update_or_create(old_id=store_old_id, defaults=store_fields)
        print store


    def import_products(self, store_id=0):
        for product in get_contentgraph_data(self._store_url(store_id=store_id) + 'product/'):

            product_default_image_old_id = product.get('default-image-id')
            if not product_default_image_old_id:
                continue

            product_old_id = product.get('id')
            product_name = product.get('name')
            product_description = product.get('description')
            product_url = product.get('url')
            product_sku = product.get('sku')
            product_price = product.get('price')

            product_fields = {'store': self.store,
                              'name': product_name,
                              'description': product_description,
                              'url': product_url, 'sku': product_sku,
                              'price': product_price}

            print 'PRODUCT - old_id: ', product_old_id, ', ', product_fields

            #the product must be created before the images as the product-images require a product
            product_psql, _, _ = Product.update_or_create(old_id=product_old_id, defaults=product_fields)

            product_image_old_ids = product.get('image-ids')
            if product_default_image_old_id not in product_image_old_ids:
                product_image_old_ids.append(product_default_image_old_id)

            for product_image_old_id in product_image_old_ids:
                product_image_fields = {'product': product_psql}

                product_image = call_contentgraph(
                    self._store_url(store_id=store_id) + 'content/' + product_image_old_id)

                product_image_url = product_image.get('url')
                product_image_original_url = product_image.get('original-url')
                product_image_dominant_color = product_image.get('dominant-colour')

                product_image_fields.update({'url': product_image_url,
                                             'original_url': product_image_original_url,
                                             'dominant_color': product_image_dominant_color})

                if self.download_images:
                    product_image_attributes, product_image_width, product_image_height = get_image_sizes(product_image)
                    product_image_fields.update({'width': product_image_width,
                                                 'height': product_image_height,
                                                 'attributes': product_image_attributes})

                print 'PRODUCT IMAGE - old_id: ', product_image_old_id, ', ', product_image_fields

                product_image_psql, _, _ = ProductImage.update_or_create(old_id=product_image_old_id,
                                                                   defaults=product_image_fields)

                if product_image_old_id == product_default_image_old_id:
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
                content_dominant_color = content.get('dominant-colour')

                content_fields.update(
                    {'url': content_url,
                     'original_url': content_original_url,
                     'source_url': content_source_url,
                     'dominant_color': content_dominant_color})

                if self.download_images:
                    content_attributes, content_width, content_height = get_image_sizes(content)
                    content_fields.update({'width': content_width,
                                           'height': content_height,
                                           'attributes': content_attributes})

                print 'IMAGE - old_id: ', content_old_id, ', ', content_fields

                content_psql, _, _ = Image.update_or_create(old_id=content_old_id, defaults=content_fields)
            elif content_type == 'video':
                content_url = content.get('original-url')
                content_source_url = content_url

                content_fields.update(
                    {'url': content_url,
                     'source_url': content_source_url,
                     'player': 'youtube'})

                print 'VIDEO - old_id: ', content_old_id, ', ', content_fields

                content_psql, _, _ = Video.update_or_create(old_id=content_old_id, defaults=content_fields)

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

            theme_psql, _, _ = Theme.update_or_create(template=page_theme_template, defaults=page_theme_fields)

            page_fields = {'feed': feed_psql, 'theme': theme_psql,
                           'name': page_name, 'legal_copy': page_legal_copy,
                           'url_slug': page_url_slug}

            print 'PAGE - old_id: ', page_old_id, ', ', page_fields

            Page.update_or_create(old_id=page_old_id, defaults=page_fields)
            self.import_tiles(page_old_id, feed_psql)


    def import_tiles(self, page_id, feed_psql):
        for tile in get_contentgraph_data('page/' + str(page_id) + '/tile/'):
            tile_old_id = tile.get('id')
            tile_template = tile.get('template')
            tile_prioritized = tile.get('prioritized') in ['true', 'True']

            tile_fields = {'feed': feed_psql, 'template': tile_template,
                           'prioritized': tile_prioritized}

            print 'TILE - old_id: ', tile_old_id, ', ', tile_fields

            tile_psql, _, _ = Tile.update_or_create(old_id=tile_old_id, defaults=tile_fields)
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

