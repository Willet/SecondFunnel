#!/usr/bin/env python

import sys, urllib2, ast

# import apps.assets.models

store_id = int(sys.argv[1])

store_psql = None
products = {}
contents = {}

headers = {'ApiKey': 'secretword'}
base_url = 'http://contentgraph-test.elasticbeanstalk.com/graph/'
base_store_url = base_url + 'store/' + str(store_id) + '/'

def getDict(url):
    request = urllib2.Request(url, None, headers)
    text = urllib2.urlopen(request).read()
    return ast.literal_eval(text)


def importStore(store_object):
    store_name = store_object.get('name')

    store_slug = store_object.get('slug')

    store_description = store_object.get('description')

    print 'STORE - name: ', store_name, ', slug: ', store_slug, ', description: ', store_description

    # store_psql = Store(name=store_name,slug=store_slug,description=store_description)
    # store_psql.save()


def importContent(content_object):
    for content in content_object:
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
            print 'IMAGE - source: ',content_source,', type: ',content_type,', source-url: ',content_source_url,', product-ids: ',content_product_ids,', name: ',content_name,', description: ',content_description,', url: ',content_url,', original-url: ',content_original_url
            # content_psql = Image(source=content_source,type=content_type,source_url=content_source_url,tagged_products=content_product_ids,name=content_name,description=content_description,original_url=content_original_url)
        else:
            print 'VIDEO - source: ',content_source,', type: ',content_type,', source-url: ',content_source_url,', product-ids: ',content_product_ids,', name: ',content_name,', description: ',content_description,', url: ',content_url
            # content_psql = Video(source=content_source,type=content_type,source_url=content_source_url,tagged_products=content_product_ids,name=content_name,description=content_description)
        # content_psql.save()
        # contents[content.get('id')] = content_psql.id
        break # remove later


def importProducts(products_object):
    for product in products_object:
        product_name = product.get('name')
        product_description = product.get('description')
        product_url = product.get('url')
        product_sku = product.get('sku')
        product_price = product.get('price')

        product_image_object = getDict(base_store_url + 'content/' + product.get('default-image-id'))

        product_image_url = product_image_object.get('url')
        product_image_original_url = product_image_object.get('original-url')
        print 'PRODUCT - name: ',product_name,', description: ',product_description,', url: ',product_url,', sku: ',product_sku,', price: ',product_price
        print 'PRODUCT IMAGE - url: ',product_image_url,', original-url: ',product_image_original_url
        # product_image_psql = ProductImage(url=product_image_url,original_url=product_image_original_url)
        # product_image_psql.save()
        # product_psql = Product(store=store_psql,name=product_name,description=product_description,url=product_url,sku=product_sku,price=product_price,default_image=product_image_psql)
        # product_psql.save()
        # products[product.get('id')] = product_psql.id
        break #remove later

def importPages(pages_object):
    for page in pages_object:
        page_name = page.get('name')
        page_legal_copy = page.get('legalCopy')

        page_theme_url = page.get('theme')

        print 'PAGE - name: ',page_name,', legal copy: ',page_legal_copy
        print 'THEME - url: ',page_theme_url
        # theme_psql = Theme(store=store_psql,template=page_theme_url)
        # page_psql = Page(theme=theme_psql,name=page_name,legal_copy=page_legal_copy)

def importer(url, import_fun):
    offset = None

    importer_url = url
    importer_object = getDict(importer_url)

    importer_results = importer_object.get('results')
    if importer_results:
        import_fun(importer_results)
        importer_cursor = importer_object.get('meta').get('cursors')

        if importer_cursor:
            offset = importer_cursor.get('next')

    else:
        import_fun(importer_object)

    while offset:
        if url.find('?') > 0:
            importer_url = url + '&offset=' + offset
        else:
            importer_url = url + '?offset=' + offset

        importer_object = getDict(importer_url)
        import_fun(importer_object.get('results'))

        importer_cursor = importer_object.get('meta').get('cursor')

        if importer_cursor:
            offset = importer_cursor.get('next')
            break # remove later
        else:
            offset = None


if __name__ == "__main__":
    importer(base_store_url, importStore)
    importer(base_store_url + 'product/', importProducts)
    importer(base_store_url + 'content/?source=dropbox', importContent)

