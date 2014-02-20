#!/usr/bin/env python

import sys

from apps.assets.models import Store, Image, Video, Product, ProductImage, Theme, Page, Feed, Tile
from apps.contentgraph.models import get_contentgraph_data
from django.core.exceptions import ObjectDoesNotExist

store_id = sys.argv[1]

store_psql = None
products = {}
contents = {}

base_store_url = 'store/' + store_id + '/'

# tries to find and then update model
# if the find fails, it creates a new model
def update_or_create(model, defaults=None, **kwargs):
    try:
        obj = model.objects.get(**kwargs)
        for key, value in defaults.iteritems():
            setattr(obj, key, value)
    except ObjectDoesNotExist:
        if defaults:
            defaults.update(kwargs)
        else:
            defaults = kwargs
        obj = model(**defaults)
    obj.save()
    return obj


def import_store():
    global store_psql
    for store in get_contentgraph_data(base_store_url):
        store_old_id = store.get('id')
        store_name = store.get('name')
        store_slug = store.get('slug')
        store_description = store.get('description')
        store_public_base_url = store.get('public-base-url')

        store_fields = {'name':store_name,'slug':store_slug,'description':store_description,'public_base_url':store_public_base_url}

        print 'STORE - old_id: ',store_old_id,', ', store_fields

        store_psql = update_or_create(Store, old_id=store_old_id, defaults=store_fields)


def import_products():
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

        product_fields = {'store':store_psql,'name':product_name,'description':product_description,'url':product_url,'sku':product_sku,'price':product_price}

        print 'PRODUCT - old_id: ',product_old_id,', ',product_fields

        #the product must be created before the images as the product-images require a product
        product_psql = update_or_create(Product, old_id=product_old_id, defaults=product_fields)

        product_image_old_ids = product.get('image-ids')
        if product_default_image_old_id not in product_image_old_ids:
            product_image_old_ids.append(product_default_image_old_id)

        product_image_fields = {'product':product_psql}

        for product_image_old_id in product_image_old_ids:
            for product_image in get_contentgraph_data(base_store_url + 'content/' + product_image_old_id):
                product_image_url = product_image.get('url')
                product_image_original_url = product_image.get('original-url')

                product_image_fields.update({'url':product_image_url,'original_url':product_image_original_url})

                print 'PRODUCT IMAGE - old_id: ',product_image_old_id,', ',product_image_fields

                update_or_create(ProductImage, old_id=product_image_old_id, defaults=product_image_fields)

        product_image_psql = ProductImage.objects.get(old_id=product_default_image_old_id)

        # setting the default product-image on the product
        product_psql.default_image_id = product_image_psql.id
        product_psql.save()
        products[product_old_id] = product_psql.id


def import_content():
    for content in get_contentgraph_data(base_store_url + 'content/'):
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
                    content_tagged_products += ',' + str(products.get(str(product_id)))
                else:
                    content_tagged_products += str(products.get(str(product_id)))

        content_name = content.get('name')
        content_description = content.get('description')

        content_fields = {'store':store_psql,'source':content_source,'tagged_products':content_tagged_products,'name':content_name,'description':content_description}

        if content_type == 'image':
            content_url = content.get('url')
            content_original_url = content.get('original-url')
            content_source_url = content.get('source-url')

            content_fields.update({'url':content_url,'original_url':content_original_url,'source_url':content_source_url})

            print 'IMAGE - old_id: ',content_old_id,', ',content_fields

            content_psql = update_or_create(Image, old_id=content_old_id, defaults=content_fields)
        elif content_type == 'video':
            content_url = content.get('original-url')
            content_source_url = content_url

            content_fields.update({'url':content_url,'source_url':content_source_url})

            print 'VIDEO - old_id: ',content_old_id,', ',content_fields

            content_psql = update_or_create(Video, old_id=content_old_id, defaults=content_fields)

        else:
            continue
        contents[content_old_id] = content_psql.id


def import_pages():
    for page in get_contentgraph_data(base_store_url + 'page/'):
        page_old_id = page.get('id')
        if not page_old_id in ['91','95','98']:
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

        page_theme_fields = {'store':store_psql}

        print 'THEME - template: ', page_theme_template,', ',page_theme_fields

        theme_psql = update_or_create(Theme, template=page_theme_template, defaults=page_theme_fields)

        page_fields = {'feed':feed_psql,'theme':theme_psql,'name':page_name,'legal_copy':page_legal_copy,'url_slug':page_url_slug}

        print 'PAGE - old_id: ',page_old_id,', ',page_fields

        update_or_create(Page, old_id=page_old_id, defaults=page_fields)
        import_tiles(page_old_id, feed_psql)


def import_tiles(page_id, feed_psql):
    for tile in get_contentgraph_data('page/' + str(page_id) + '/tile/'):
        tile_old_id = tile.get('id')
        tile_template = tile.get('template')
        tile_prioritized = tile.get('prioritized') in ['true', 'True']

        tile_fields = {'feed':feed_psql,'template':tile_template,'prioritized':tile_prioritized}

        print 'TILE - old_id: ',tile_old_id,', ',tile_fields

        tile_psql = update_or_create(Tile, old_id=tile_old_id, defaults=tile_fields)
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

if __name__ == "__main__":
    import_store()
    import_products()
    import_content()
    import_pages()

