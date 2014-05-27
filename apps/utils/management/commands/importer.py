"""
To import store, products, content, tiles, and themes from store 38, type:
$ ./manage.py importer 38 true
"""
import cStringIO
import datetime
import json
import pytz
import urllib
from django.conf import settings

try:  # this one fails in virtualenvs whose PIL was compiled before Pillow
    from PIL import Image as Img
except ImportError as err:
    from PIL.PIL import Image as Img

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


        self.import_store()
        if('store' in args):
            return
        elif any(s in args for s in ['products', 'content', 'pages']):
            if 'products' in args:
                self.import_products()
            if 'content' in args:
                self.import_content()
            if 'pages' in args:
                self.import_pages()
        else:  # only store id and download images supplied
            self.import_products()
            self.import_content()
            self.import_pages()


    def _store_url(self, store_id=None):
        """returns CG url for a store, or if no store, then all stores."""
        store_id = store_id or self.store_id
        if store_id:
            return 'store/{0}/'.format(store_id)
        else:
            return 'store/'

    def import_store(self, store_id=None):
        store_id = store_id or self.store_id
        store_dict = call_contentgraph(self._store_url())
        store_old_id = store_dict.get('id')
        store_name = store_dict.get('name')
        store_slug = store_dict.get('slug')
        store_description = store_dict.get('description')
        store_public_base_url = store_dict.get('public-base-url')

        store_fields = {'name': store_name, 'slug': store_slug,
                        'description': store_description,
                        'public_base_url': store_public_base_url}

        print 'STORE - old_id: ', store_old_id, ', ', store_fields

        self.store, _, _ = Store.update_or_create(old_id=store_old_id, defaults=store_fields)


    def import_products(self, store_id=None):
        store_id = store_id or self.store_id
        for product_dict in get_contentgraph_data(self._store_url() + 'product/'):

            product_default_image_old_id = product_dict.get('default-image-id')
            if not product_default_image_old_id:
                continue

            product_old_id = product_dict.get('id')
            product_name = product_dict.get('name')
            product_description = product_dict.get('description')
            product_url = product_dict.get('url')
            product_sku = product_dict.get('sku')
            product_price = product_dict.get('price')

            product_fields = {'store': self.store,
                              'name': product_name,
                              'description': product_description,
                              'url': product_url, 'sku': product_sku,
                              'price': product_price}

            print 'PRODUCT - old_id: ', product_old_id, ', ', product_fields

            #the product must be created before the images as the product-images require a product
            product, _, _ = Product.update_or_create(old_id=product_old_id, defaults=product_fields)

            product_image_old_ids = product_dict.get('image-ids')
            if product_default_image_old_id not in product_image_old_ids:
                product_image_old_ids.append(product_default_image_old_id)

            for product_image_old_id in product_image_old_ids:
                product_image_fields = {'product': product}

                product_image = call_contentgraph(
                    self._store_url(store_id=store_id) + 'content/' + product_image_old_id)

                product_image_url = product_image.get('url')
                product_image_original_url = product_image.get('original-url')
                product_image_dominant_color = product_image.get('dominant-color') or \
                                               product_image.get('dominant-colour')

                product_image_fields.update({'url': product_image_url,
                                             'original_url': product_image_original_url,
                                             'dominant_color': product_image_dominant_color})

                if self.download_images:
                    product_image_attributes, product_image_width, product_image_height = get_image_sizes(product_image)
                    product_image_fields.update({'width': product_image_width,
                                                 'height': product_image_height,
                                                 'attributes': product_image_attributes})

                print 'PRODUCT IMAGE - old_id: ', product_image_old_id, ', ', product_image_fields

                product_image, _, _ = ProductImage.update_or_create(old_id=product_image_old_id,
                                                                    defaults=product_image_fields)

                if product_image_old_id == product_default_image_old_id:
                    product.default_image_id = product_image.id
                    product.save()

            products[product_old_id] = product.id


    def import_content(self, store_id=None):
        store_id = store_id or self.store_id
        for content_dict in get_contentgraph_data(self._store_url() + 'content/'):
            content_old_id = content_dict.get('id')
            content_source = content_dict.get('source')
            # if the image has source 'image' (product image), skip
            if content_source == 'image':
                continue

            content_type = content_dict.get('type')

            content_name = content_dict.get('name')
            content_status = content_dict.get('status', 'approved')
            content_description = content_dict.get('description')

            content_fields = {'store': self.store,
                              'source': content_source,
                              'name': content_name,
                              'status': content_status,
                              'description': content_description}

            if content_type == 'image':

                content_url = content_dict.get('url')
                content_original_url = content_dict.get('original-url')
                content_source_url = content_dict.get('source-url')
                content_dominant_color = content_dict.get('dominant-color') or \
                                         content_dict.get('dominant-colour')

                content_fields.update(
                    {'url': content_url,
                     'original_url': content_original_url,
                     'source_url': content_source_url,
                     'dominant_color': content_dominant_color})

                if self.download_images:
                    content_attributes, content_width, content_height = get_image_sizes(content_dict)
                    content_fields.update({'width': content_width,
                                           'height': content_height,
                                           'attributes': content_attributes})

                print 'IMAGE - old_id: ', content_old_id, ', ', content_fields

                content, _, _ = Image.update_or_create(old_id=content_old_id, defaults=content_fields)
            elif content_type == 'video':
                content_original_id = content_dict.get('original-id')
                content_url = content_dict.get('original-url')
                content_source_url = content_url

                content_fields.update({
                    'url': content_url,
                    'username': content_dict.get('username', ''),
                    'caption': content_dict.get('caption', ''),
                    'original_id': content_original_id,
                    'source_url': content_source_url,
                    'player': 'youtube'})

                print 'VIDEO - old_id: ', content_old_id, ', ', content_fields

                content, _, _ = Video.update_or_create(old_id=content_old_id, defaults=content_fields)

            else:
                continue

            content_products_object = content_dict.get('tagged-products')
            if content_products_object:
                for product_old_id in content_products_object:
                    if products.get(str(product_old_id)):
                        content.tagged_products.add(products[product_old_id])
                    else:
                        print "Product #{0} not found".format(product_old_id)

            contents[content_old_id] = content.id


    def import_pages(self, store_id=None):
        store_id = store_id or self.store_id
        for page_dict in get_contentgraph_data(self._store_url() + 'page/'):
            page_old_id = page_dict.get('id')
            if not page_old_id in ['53', '91', '95', '98', '102']:
                continue
            page_name = page_dict.get('name')
            page_legal_copy = page_dict.get('legalCopy')
            page_product_desc = page_dict.get('featured-product-description', '')
            page_img_tile_wide = page_dict.get('imageTileWide', 0.5)
            page_desktop_hero_image = page_dict.get('heroImageDesktop', '')
            page_mobile_hero_image = page_dict.get('heroImageMobile', '')
            page_results_threshold = page_dict.get('results_threshold', "{}")
            page_intentrank_id = page_dict.get('intentrank_id', "")
            page_url_slug = page_dict.get('url')
            page_theme_template = page_dict.get('theme')
            page_column_width = page_dict.get('column-width')
            page_social_buttons = page_dict.get('social-buttons')
            page_enable_tracking = page_dict.get('enable-tracking')
            page_hide_navigation_bar = page_dict.get('hide-navigation-bar')

            # since feeds have no fields except id right now, the only way to find the feed is based on the page's feed_id
            try:
                page = Page.objects.get(old_id=page_old_id)
                feed = Feed.objects.get(id=page.feed_id)
            except Page.DoesNotExist:
                feed = Feed()

            feed.feed_algorithm = page_dict.get('ir-algorithm', 'generic')
            feed.save()

            page_theme_fields = {}

            print 'THEME - template: ', page_theme_template, ', ', page_theme_fields

            theme, _, _ = Theme.update_or_create(template=page_theme_template, defaults=page_theme_fields)

            page_fields = {'store': self.store,
                           'feed': feed,
                           'theme': theme,
                           'name': page_name,
                           'description': page_legal_copy or page_product_desc,
                           'legal_copy': page_legal_copy,
                           'url_slug': page_url_slug}

            print 'PAGE - old_id: ', page_old_id, ', ', page_fields

            page, _, _ = Page.update_or_create(old_id=page_old_id, defaults=page_fields)
            page.image_tile_wide = page_img_tile_wide  # save JSON fields
            page.desktop_hero_image = page_desktop_hero_image
            page.mobile_hero_image = page_mobile_hero_image
            page.results_threshold = page_results_threshold
            page.intentrank_id = page_intentrank_id
            page.column_width = page_column_width
            page.social_buttons = page_social_buttons
            page.enable_tracking = page_enable_tracking
            page.hide_navigation_bar = page_hide_navigation_bar
            page.save()

            self.import_tiles(page_old_id, feed)


    def import_tiles(self, page_id, feed):
        for tile_dict in get_contentgraph_data('page/' + str(page_id) + '/tile/'):
            tile_old_id = tile_dict.get('id')
            tile_template = tile_dict.get('template')
            tile_prioritized = "pageview" if tile_dict.get('prioritized') in ['true', 'True'] else ""
            tile_priority = tile_dict.get('priority', 0)
            tile_created_at = tile_dict.get('created')
            tile_updated_at = tile_dict.get('last-modified')

            tile_fields = {'feed': feed, 'template': tile_template,
                           'prioritized': tile_prioritized,
                           'priority': tile_priority, }

            # read redirect-url (among others) for banner tiles' stringified json
            if tile_template == "banner":
                tile_fields['attributes'] = tile_dict.get('json')

            print 'TILE - old_id: ', tile_old_id, ', ', tile_fields

            tile, _, _ = Tile.update_or_create(old_id=tile_old_id, defaults=tile_fields)
            tile_content_old_ids = tile_dict.get('content-ids')
            if tile_content_old_ids:
                for content_old_id in tile_content_old_ids:
                    if contents.get(str(content_old_id)):
                        tile.content.add(contents[str(content_old_id)])
                    else:
                        print "Content #{0} not found".format(content_old_id)
            tile_product_old_ids = tile_dict.get('product-ids')
            if tile_product_old_ids:
                for product_old_id in tile_product_old_ids:
                    if products.get(str(product_old_id)):
                        tile.products.add(products[str(product_old_id)])
                    else:
                        print "Product #{0} not found".format(product_old_id)

            if tile_created_at:
                # order imported tiles by CG's created date
                tile.created_at = datetime.datetime.fromtimestamp(
                    float(tile_created_at) / 1000,
                    tz=pytz.timezone(settings.TIME_ZONE))
            if tile_updated_at:
                # order imported tiles by CG's modified date
                tile.updated_at = datetime.datetime.fromtimestamp(
                    float(tile_updated_at) / 1000,
                    tz=pytz.timezone(settings.TIME_ZONE))
            tile.save()
