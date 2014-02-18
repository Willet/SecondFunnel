#!/usr/bin/env python

import sys

import apps.assets.models
from apps.contentgraph.models import get_contentgraph_data

store_id = int(sys.argv[1])

store_psql = None
products = {}
contents = {}

base_store_url = 'store/' + str(store_id) + '/'


def importStore():
    for store in get_contentgraph_data(base_store_url):
        store_name = store.get('name')

        store_slug = store.get('slug')

        store_description = store.get('description')

        print 'STORE - name: ', store_name, ', slug: ', store_slug, ', description: ', store_description

        # store_psql = Store(name=store_name,slug=store_slug,description=store_description)
        # store_psql.save()


def importContent():
    for content in get_contentgraph_data(base_store_url + 'content/'):
        content_source = content.get('source')
        if content_source == 'image':
            continue
        content_type = content.get('type')
        content_source_url = content.get('source-url')
        content_products_object = content.get('tagged-products')
        content_product_ids = ''
        for product_id in content_products_object:
            if len(content_product_ids) > 0:
                content_product_ids += ',' + str(products.get(str(product_id)))
            else:
                content_product_ids += str(products.get(str(product_id)))

        content_name = content.get('name')
        content_description = content.get('description')
        content_url = content.get('url')
        # content_file_type = content_object.get
        if content_type == 'image':
            content_original_url = content.get('original-url')
            print 'IMAGE - source: ', content_source, ', type: ', content_type, ', source-url: ', content_source_url, ', product-ids: ', content_product_ids, ', name: ', content_name, ', description: ', content_description, ', url: ', content_url, ', original-url: ', content_original_url
            # content_psql = Image(source=content_source,type=content_type,source_url=content_source_url,tagged_products=content_product_ids,name=content_name,description=content_description,original_url=content_original_url)
        else:
            print 'VIDEO - source: ', content_source, ', type: ', content_type, ', source-url: ', content_source_url, ', product-ids: ', content_product_ids, ', name: ', content_name, ', description: ', content_description, ', url: ', content_url
            # content_psql = Video(source=content_source,type=content_type,source_url=content_source_url,tagged_products=content_product_ids,name=content_name,description=content_description)
        # content_psql.save()
        # contents[content.get('id')] = content_psql.id
        break  # remove later


def importProducts():
    for product in get_contentgraph_data(base_store_url + 'product/'):
        product_name = product.get('name')
        product_description = product.get('description')
        product_url = product.get('url')
        product_sku = product.get('sku')
        product_price = product.get('price')

        for product_image_object in get_contentgraph_data(
                                base_store_url + 'content/' + product.get('default-image-id')):
            product_image_url = product_image_object.get('url')
            product_image_original_url = product_image_object.get('original-url')
        print 'PRODUCT - name: ', product_name, ', description: ', product_description, ', url: ', product_url, ', sku: ', product_sku, ', price: ', product_price
        print 'PRODUCT IMAGE - url: ', product_image_url, ', original-url: ', product_image_original_url
        # product_image_psql = ProductImage(url=product_image_url,original_url=product_image_original_url)
        # product_image_psql.save()
        # product_psql = Product(store=store_psql,name=product_name,description=product_description,url=product_url,sku=product_sku,price=product_price,default_image=product_image_psql)
        # product_psql.save()
        # products[product.get('id')] = product_psql.id
        break  #remove later


def importPages():
    for page in get_contentgraph_data(base_store_url + 'page/'):
        page_name = page.get('name')
        page_legal_copy = page.get('legalCopy')

        page_theme_url = page.get('theme')

        print 'PAGE - name: ', page_name, ', legal copy: ', page_legal_copy
        print 'THEME - url: ', page_theme_url
        # theme_psql = Theme(store=store_psql,template=page_theme_url)
        # page_psql = Page(theme=theme_psql,name=page_name,legal_copy=page_legal_copy)
        break  # remove later


if __name__ == "__main__":
    importStore()
    importProducts()
    importContent()
    importPages()
    #importer(base_store_url, importStore)
    #importer(base_store_url + 'product/', importProducts)
    #importer(base_store_url + 'content/?source=dropbox', importContent)

