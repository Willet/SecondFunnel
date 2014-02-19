#!/usr/bin/env python

import sys

from apps.assets.models import Store, Image, Video, Product, ProductImage, Theme, Page, Feed, Tile
from apps.contentgraph.models import get_contentgraph_data

store_id = sys.argv[1]

store_psql = None
products = {}
contents = {}

base_store_url = 'store/' + store_id + '/'


def importStore():
    global store_psql
    for store in get_contentgraph_data(base_store_url):
        store_old_id = store.get('id')
        store_name = store.get('name')
        store_slug = store.get('slug')
        store_description = store.get('description')
        store_public_base_url = store.get('public-base-url')

        print 'STORE - old_id: ',store_old_id,', name: ', store_name, ', slug: ', store_slug, ', description: ', store_description, ', public_base_url: ', store_public_base_url

        try:
            store_psql = Store.objects.get(old_id=store_old_id)
            store_psql_id = store_psql.id
        except Store.DoesNotExist:
            store_psql_id = None
        store_psql = Store(id=store_psql_id,old_id=store_old_id,name=store_name,slug=store_slug,description=store_description,public_base_url=store_public_base_url)
        store_psql.save()


def importContent():
    for content in get_contentgraph_data(base_store_url + 'content/'):
        content_old_id = content.get('id')
        content_source = content.get('source')
        if content_source == 'image':
            continue
        content_type = content.get('type')
        content_source_url = content.get('source-url')
        content_products_object = content.get('tagged-products')
        content_product_ids = ''
        if content_products_object:
            for product_id in content_products_object:
                if len(content_product_ids) > 0:
                    content_product_ids += ',' + str(products.get(str(product_id)))
                else:
                    content_product_ids += str(products.get(str(product_id)))

        content_name = content.get('name')
        content_description = content.get('description')

        if content_type == 'image':
            content_url = content.get('url')
            content_original_url = content.get('original-url')

            print 'IMAGE - old_id: ',content.get('id'),', source: ', content_source, ', source-url: ', content_source_url, ', product-ids: ', content_product_ids, ', name: ', content_name, ', description: ', content_description, ', url: ', content_url, ', original-url: ', content_original_url

            try:
                content_psql = Image.objects.get(old_id=content_old_id)
                content_psql_id = content_psql.id
            except Image.DoesNotExist:
                content_psql_id = None
            content_psql = Image(id=content_psql_id,old_id=content_old_id,store=store_psql,source=content_source,source_url=content_source_url,tagged_products=content_product_ids,name=content_name,description=content_description,url=content_url,original_url=content_original_url)
        elif content_type == 'video':
            content_url = content.get('original-url')

            print 'VIDEO - old_id: ',content.get('id'),', source: ', content_source, ', source-url: ', content_source_url, ', product-ids: ', content_product_ids, ', name: ', content_name, ', description: ', content_description, ', url: ', content_url,',player: youtube'

            try:
                content_psql = Video.objects.get(old_id=content_old_id)
                content_psql_id = content_psql.id
            except Video.DoesNotExist:
                content_psql_id = None
            content_psql = Video(id=content_psql_id,old_id=content_old_id,store=store_psql,source=content_source,source_url=content_source_url,tagged_products=content_product_ids,name=content_name,url=content_url,description=content_description,player='youtube')
        else:
            continue
        content_psql.save()
        contents[content.get('id')] = content_psql.id


def importProducts():
    for product in get_contentgraph_data(base_store_url + 'product/'):
        product_old_id = product.get('id')
        product_name = product.get('name')
        product_description = product.get('description')
        product_url = product.get('url')
        product_sku = product.get('sku')
        product_price = product.get('price')

        product_default_image_old_id = product.get('default-image-id')
        if not product_default_image_old_id:
            continue

        print 'PRODUCT - old_id: ',product_old_id,', name: ', product_name, ', description: ', product_description, ', url: ', product_url, ', sku: ', product_sku, ', price: ', product_price

        try:
            product_psql = Product.objects.get(old_id=product_old_id)
            product_psql_id = product_psql.id
        except Product.DoesNotExist:
            product_psql_id = None
        product_psql = Product(id=product_psql_id,old_id=product_old_id,store=store_psql,name=product_name,description=product_description,url=product_url,sku=product_sku,price=product_price)
        product_psql.save()

        for product_image_old_id in product.get('image-ids'):
            for product_image in get_contentgraph_data(base_store_url + 'content/' + product_image_old_id):
                product_image_url =  product_image.get('url')
                product_image_original_url = product_image.get('original-url')

                print 'PRODUCT IMAGE - old_id: ',product_image_old_id,', url: ', product_image_url, ', original-url: ', product_image_original_url

                try:
                    product_image_psql = ProductImage.objects.get(old_id=product_image_old_id)
                    product_image_psql_id = product_image_psql.id
                except ProductImage.DoesNotExist:
                    product_image_psql_id = None
                product_image_psql = ProductImage(id=product_image_psql_id,old_id=product_image_old_id,product=product_psql,url=product_image_url,original_url=product_image_original_url)
                product_image_psql.save()

        product_image_psql = ProductImage.objects.get(old_id=product_default_image_old_id)
        product_psql.default_image_id = product_image_psql.id
        product_psql.save()
        products[product.get('id')] = product_psql.id


def importPages():
    for page in get_contentgraph_data(base_store_url + 'page/'):
        page_old_id = page.get('id')
        if not page_old_id in ['91','95','98']:
            continue
        page_name = page.get('name')
        page_legal_copy = page.get('legalCopy')
        page_url_slug = page.get('url')
        page_theme_template = page.get('theme')

        print 'PAGE - id',page.get('id'),'name: ', page_name, ', legal copy: ', page_legal_copy, ', url_slug: ', page_url_slug
        print 'THEME - template: ', page_theme_template

        try:
            page_psql = Page.objects.get(old_id=page_old_id)
            page_psql_id = page_psql.id
            feed_psql = Feed.objects.get(id=page_psql.feed_id)
        except Page.DoesNotExist:
            page_psql_id = None
            feed_psql = Feed()
            feed_psql.save()
        try:
            theme_psql = Theme.objects.get(template=page_theme_template)
        except Theme.DoesNotExist:
            theme_psql = Theme(store=store_psql, template=page_theme_template)
            theme_psql.save()
        page_psql = Page(id=page_psql_id,old_id = page_old_id,feed=feed_psql,theme=theme_psql,name=page_name,url_slug=page_url_slug,legal_copy=page_legal_copy)
        page_psql.save()
        importTiles(page.get('id'), feed_psql)


def importTiles(page_id, feed_psql):
    for tile in get_contentgraph_data('page/' + str(page_id) + '/tile/'):
        tile_old_id = tile.get('id')
        tile_template = tile.get('template')
        tile_prioritized = tile.get('prioritized') in ['true', 'True']

        print 'TILE - id: ',tile_old_id,'template: ',tile_template,', prioritized: ', tile_prioritized

        try:
            tile_psql = Tile.objects.get(old_id=tile_old_id)
            tile_psql_id = tile_psql.id
        except Tile.DoesNotExist:
            tile_psql_id = None
        tile_psql = Tile(id=tile_psql_id,old_id=tile_old_id,feed=feed_psql,template=tile_template,prioritized=tile_prioritized)
        tile_psql.save()
        tile_content_ids = tile.get('content-ids')
        if tile_content_ids:
            for content_id in tile_content_ids:
                if contents.get(str(content_id)):
                    tile_psql.content.add(contents[str(content_id)])
        tile_product_ids = tile.get('product-ids')
        if tile_product_ids:
            for product_id in tile_product_ids:
                if products.get(str(product_id)):
                    tile_psql.products.add(products[str(product_id)])

if __name__ == "__main__":
    importStore()
    importProducts()
    importContent()
    importPages()

