import random

from apps.assets.models import Store, Product, ProductImage
from apps.imageservice.utils import get_filetype, upload_to_cloudinary

from .rakuten import RakutenDatafeed

class BodyShopDatafeed(RakutenDatafeed):
    name = 'bodyshop'

    def __init__(self):
        store = Store.objects.get(slug=self.name)
        datafeed = {
            'filename': '13962_3263197_mp.txt.gz',
            'pathname': '',
            'field_mapping': ['SKU',
                     'NAME',
                     'ID',
                     'category',
                     'ADVERTISERCATEGORY',
                     'BUYURL',
                     'ARTIST',
                     '',
                     'DESCRIPTION',
                     'description v2?',
                     '',
                     '',
                     'PRICE',
                     'SALEPRICE',
                     '',
                     '',
                     '"the body shop"',
                     'different price',
                     '',
                     'numbers?? v2',
                     '"the body shop" v2',
                     '',
                     'INSTOCK']
        }
        super(BodyShopDatafeed, self).__init__(store=store, datafeed=datafeed)

    def load(self, options={}):
        """ Import data feed & generate lookup table 
        # BUYURL - product url
        # ADVERTISERCATEGORY - product category breadcrumb
        # ARTIST - large product image url
        """
        self.options = options

        self.lookup_table = super(BodyShopDatafeed, self).load(
            collect_fields=["ID", "NAME", "DESCRIPTION", "PRICE",
                "SALEPRICE", "BUYURL", "INSTOCK",
                "ADVERTISERCATEGORY", "ARTIST"],
            lookup_fields=["ID","NAME","ADVERTISERCATEGORY"])
    
    def lookup_product(self, product):
        """ Looksup product in datafeed

        Returns:
            match: (product_data <dict>, matched_field <str>)
            no-match: (None, None)
        """
        return self.lookup_table.find(
            mappings=[
                ("ID", product.sku),
                ("NAME", "The Body Shop {}".format(product.name.encode('ascii', errors='ignore'))),
            ], first=True)

    def update_product(self, product, data):
        """ Updates product with data """
        self._update_product_rakuten_fields(product, data)

        if product.in_stock and self.options.get('similar_products', False):
            print "Generating similar products"
            self._update_similar_products(product, data)

    @staticmethod
    def _update_product_rakuten_fields(product, data):
        # product price should always be the largest price on record
        # so that products appear to be more on sale
        new_price = float(data['PRICE'])
        if new_price > product.price:
            product.price = new_price
        product.sale_price = float(data['SALEPRICE'])
        product.in_stock = True if data['INSTOCK'] == 'in-stock' else False
        product.attributes['affiliate_link'] = data['BUYURL']

    def _update_similar_products(self, product, data, max_num=3):
        """
        Update existing similar products and replace sold out similar products
        If there are no similar products, generate max_num of new ones
        """
        exclude_skus = []
        generate_similar_products_num = max_num

        if product.similar_products.count():
            sold_out_products = []

            # Update existing similar products
            for sp in product.similar_products.all():
                (sp_data, _) = self.lookup_table.find(mappings=[("SKU", sp.sku)], first=True)
                if sp_data:
                    self._update_product_rakuten_fields(sp, sp_data)
                else:
                    sp.in_stock = False
                sp.save()

                exclude_skus.append(sp.sku)

                if not sp.in_stock:
                    sold_out_products.append(sp)

            # Removed sold out products
            product.similar_products.remove(*sold_out_products)
            generate_similar_products_num = max_num - product.similar_products.count()


        if generate_similar_products_num:
            # Generate new similar products
            similar_products_data = self._get_similar_products_data(data)
            # Filter out existing similar products
            similar_products_data = [ sp for sp in similar_products_data if sp['SKU'] not in exclude_skus ]
            try:
                # Randomly select 3 similar products out of the options
                similar_products_data = random.sample(similar_products_data, generate_similar_products_num)
            except ValueError:
                pass # Less than 3 similar products
            new_similar_products = [ self._update_or_create_similar_product(sp, product.store) for sp in similar_products_data ]
            product.similar_products.add(*new_similar_products)

    def _update_or_create_similar_product(self, data, store):
        """
        Try to find similar product based on SKU, then updated with data
        If created, generate product image
        """
        try:
            product = Product.objects.get(sku=data['SKU'],
                                          store= store)
        except Product.DoesNotExist:
            product = Product(sku= data['SKU'],
                              url= data['BUYURL'],
                              name= data['NAME'],
                              store= store)

        # Update
        self._update_product_rakuten_fields(product, data)
        product.save()

        if not product.product_images.count():
            # Add one product image
            # TODO: utilize cloudinary
            product_image_url = data['ARTIST']
            data = upload_to_cloudinary(product_image_url)
            product_image = ProductImage(product= product,
                                         url= data.get('url', product_image_url),
                                         original_url= product_image_url,
                                         file_type= get_filetype(data.get('url', product_image_url)),
                                         attributes= {
                                            'sizes': {
                                                'master': {
                                                    'width': data.get('width', 430),
                                                    'height': data.get('height', 430),
                                                },
                                            },
                                         })
            product_image.save()
            product.default_image = product_image
            product.save()

        return product

    def _get_similar_products_data(self, product_data):
        """
        Get similar product data for the product in product_data
        """
        mapping = ("ADVERTISERCATEGORY", product_data["ADVERTISERCATEGORY"])
        # get similar products data, guarenteed to be at least the same product
        (similar_products_data, _) = self.lookup_table.find(mappings=[mapping], first=False)
        # remove same product from similar_products
        similar_products_data.remove(product_data)
        # remove out of stock similar products
        similar_products_data = [ sp for sp in similar_products_data if sp['INSTOCK'] == 'in-stock' ]
        
        return similar_products_data
