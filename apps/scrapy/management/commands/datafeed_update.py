import random

from django.core.management.base import BaseCommand
from django.db import transaction
from optparse import make_option

from apps.assets.models import Page, Product, ProductImage
from apps.imageservice.utils import get_filetype
from apps.scrapy.datafeed.cj import download_product_datafeed, load_product_datafeed, delete_product_datafeed
from apps.scrapy.logging import notify_slack, upload_to_s3

# Required to use scrapy logging
class FakeSpider(object):
    """ Emulte spider keys """
    def __init__(self, name):
        self.name = name


class FakeLog(object):
    def getvalue(self):
        return ""


class Command(BaseCommand):
    help = """Updates products from a CJ product data feed
    Usage:
    python manage.py datafeed_update <url_slug>

    url_slug
        Url slug of the page to update
    """
    @staticmethod
    def update_product_cj_fields(product, data):
        product.price = float(data['PRICE'])
        product.sale_price = float(data['SALEPRICE'])
        product.in_stock = True if data['INSTOCK'] == 'yes' else False
        product.attributes['cj_link'] = data['BUYURL']

    def update_or_create_similar_product(self, data, store):
        """
        Try to find similar product based on SKU, then updatd with data
        If created, generate product image
        """
        try:
            product = Product.objects.get(sku=data['SKU'],
                                          store= store)
        except Product.DoesNotExist:
            product = Product(sku= data['SKU'],
                              url= data['THIRDPARTYCATEGORY'],
                              name= data['NAME'],
                              store= store)

        # Update
        self.update_product_cj_fields(product, data)
        product.save()

        if not product.product_images.count():
            # Add one product image
            # TODO: utilize cloudinary
            product_image_url = data['ARTIST']
            product_image = ProductImage(product= product,
                                         url= product_image_url,
                                         original_url= product_image_url,
                                         file_type= get_filetype(product_image_url),
                                         attributes= {
                                            'sizes': {
                                                'master': {
                                                    'width': 430,
                                                    'height': 430,
                                                },
                                            },
                                         })
            product_image.save()
            product.default_image = product_image
            product.save()

        return product

    def get_similar_products_data(self, product_data):
        """
        Get similar product data for the product in product_data
        """
        mapping = ("ADVERTISERCATEGORY", product_data["ADVERTISERCATEGORY"])
        # get similar products data, gaurenteed to be at least the same product
        (similar_products_data, _) = self.lookup_table.find(mappings=[mapping], first=False)
        # remove same product from similar_products
        similar_products_data.remove(product_data)
        # remove out of stock similar products
        similar_products_data = [ sp for sp in similar_products_data if sp['INSTOCK'] == 'yes' ]

        return similar_products_data

    def update_similar_products(self, product, data, max_num=3):
        """
        Update existing similar products and replace sold out similar products
        If there are no similar products, generate max_num of new ones
        """
        exclude_skus = []
        generate_similar_products_num = 3

        if product.similar_products.count():
            sold_out_products = []

            # Update existing similar products
            for sp in product.similar_products.all():
                (sp_data, _) = self.lookup_table.find(mappings=[("SKU", sp.sku)], first=True)
                self.update_product_cj_fields(sp, sp_data)
                sp.save()

                exclude_skus.append(sp.sku)

                if not sp.in_stock:
                    sold_out_products.append(sp)

            # Removed sold out products
            product.similar_products.remove(*sold_out_products)
            generate_similar_products_num = max_num - product.similar_products.count()


        if generate_similar_products_num:
            # Generate new similar products
            similar_products_data = self.get_similar_products_data(data)
            # Filter out existing similar products
            similar_products_data = [ sp for sp in similar_products_data if sp['SKU'] not in exclude_skus ]
            try:
                # Randomly select 3 similar products out of the options
                similar_products_data = random.sample(similar_products_data, generate_similar_products_num)
            except ValueError:
                pass # Less than 3 similar products
            new_similar_products = [ self.update_or_create_similar_product(sp, product.store) for sp in similar_products_data ]
            product.similar_products.add(*new_similar_products)
    
    def update_product(self, product, data):
        self.update_product_cj_fields(product, data)

        if product.in_stock:
            self.update_similar_products(product, data)
    
    def handle(self, url_slug, **options):
        page = Page.objects.get(url_slug=url_slug)
        results = {
            'logging/errors': {},
            'logging/items dropped': [],
            'logging/items out of stock': [],
            'logging/items updated': [],
            'logging/new items': [],
            'log': FakeLog(),
        }

        # Grab CJ Product Data Feed
        product_datafeed_filename = download_product_datafeed(page.store)

        # Import data feed & generate lookup table
        # THIRDPARTYCATEGORY - product url
        # ADVERTISERCATEGORY - product category breadcrumb
        # ARTIST - large product image url
        self.lookup_table = load_product_datafeed(filename=product_datafeed_filename,
                                            collect_fields=["SKU", "NAME", "DESCRIPTION", "PRICE",
                                                            "SALEPRICE", "BUYURL", "INSTOCK",
                                                            "ADVERTISERCATEGORY", "THIRDPARTYCATEGORY",
                                                            "ARTIST"],
                                             lookup_fields=["SKU","NAME","THIRDPARTYCATEGORY",
                                                            "ADVERTISERCATEGORY"])
        try:
            products = page.feed.get_all_products()
            print u"Found {} products for {}".format(len(products), url_slug)

            # Find product in product data feed & update
            with transaction.atomic():
                for product in products:
                    match = field = val = None
                    try:
                        match = self.lookup_table.find(mappings=[
                                ("SKU", product.sku),
                                ("NAME", product.name.encode('ascii', errors='ignore')),
                                ("THIRDPARTYCATEGORY", product.url),
                            ],
                            first=True)
                    except Exception as e:
                        errors = results['logging/errors']
                        msg = '{}: {}'.format(e.__class__.__name__, e)
                        items = errors.get(msg, [])
                        items.append(product.url)
                        errors[msg] = items
                        results['logging/errors'] = errors
                        print 'logging/errors: {}'.format(msg)
                    else:
                        data, field = match
                        if data:
                            # Found matching product
                            print u"{} match: {}".format(field, product.url)

                            self.update_product(product, data)
                            product.save()

                            if product.in_stock:
                                results['logging/items updated'].append(product.url)
                            else:
                                results['logging/items out of stock'].append(product.url)
                        else:
                            print u"\tMatch FAILED: {} {}".format(product.name.encode('ascii', errors='ignore'), product.url)
                            # Out of stock items often just disappear from the feeds
                            if product.in_stock:
                                product.in_stock = False
                                product.save()
                                # If an item just switched, record it that way
                                results['logging/items out of stock'].append(product.url)
                            else:
                                # If the item previously was out of stock, call it dropped
                                results['logging/items dropped'].append(product.url)

            print "Updates saved"

            spider = FakeSpider("CJ Sur La Table Datafeed")
            reason = "finished"

            # Save results
            summary_url, log_url = upload_to_s3.S3Logger(
                results,
                spider,
                reason
            ).run()

            notify_slack.dump_stats(
                results,
                spider,
                reason,
                (summary_url, log_url)
            )
        finally:
            # Whatever happened, delete the file
            delete_product_datafeed(product_datafeed_filename)
