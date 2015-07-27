from apps.scrapy.datafeeds.cj import Datafeed


class SurLaTableDatafeed(Datafeed):
    name = 'surlatable'

    def __init__(self):
        store = Store.objects.get(slug=name)
        datafeed = {
            "PATHNAME": "outgoing/productcatalog/170707/",
            "FILENAME": "Sur_La_Table-Sur_La_Table_Product_Catalog.txt.gz",
        }
        super(SurLaTableDatafeed, self).__init__(store=store, datafeed=datafeed)

    def load(self):
        """ Import data feed & generate lookup table """
        # THIRDPARTYCATEGORY - product url
        # ADVERTISERCATEGORY - product category breadcrumb
        # ARTIST - large product image url
        self.lookup_table = super(SurLaTableDatafeed, self).load(
            collect_fields=["SKU", "NAME", "DESCRIPTION", "PRICE",
                "SALEPRICE", "BUYURL", "INSTOCK",
                "ADVERTISERCATEGORY", "THIRDPARTYCATEGORY",
                "ARTIST"],
            lookup_fields=["SKU","NAME","THIRDPARTYCATEGORY", "ADVERTISERCATEGORY"]))
    
    def lookup_product(self, product):
        """ Looksup product in datafeed

        Returns:
            match: (product_data <dict>, matched_field <str>)
            no-match: (None, None)
        """
        return self.lookup_table.find(
            mappings=[
                ("SKU", product.sku),
                ("NAME", product.name.encode('ascii', errors='ignore')),
                ("THIRDPARTYCATEGORY", product.url),
            ], first=True)

    def update_product(self, product, data):
        """ Updates product with data """
        self._update_product_cj_fields(product, data)

        if product.in_stock:
            self._update_similar_products(product, data)

    @staticmethod
    def _update_product_cj_fields(product, data):
        product.price = float(data['PRICE'])
        product.sale_price = float(data['SALEPRICE'])
        product.in_stock = True if data['INSTOCK'] == 'yes' else False
        product.attributes['cj_link'] = data['BUYURL']

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
                self._update_product_cj_fields(sp, sp_data)
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

    def _get_similar_products_data(self, product_data):
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
