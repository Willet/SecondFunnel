from django.conf.urls import patterns, url

urlpatterns = patterns('apps.contentgraph.views',
    url(r'^store/?$',
        'view_stores', name='view_stores'),
    url(r'^store/(?P<store_id>\d+)/?$',
        'view_store', name='view_store'),

    url(r'^store/(?P<store_id>\d+)/page/?$',
        'view_pages', name='view_pages'),
    url(r'^store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/?$',
        'view_page', name='view_page'),

    url(r'^store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/?$',
        'view_products', name='view_products'),
    url(r'^store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/(?P<product_id>\d+)/?$',
        'view_product', name='view_product'),

    # last
    url(r'^(?P<endpoint_path>.+)$',
        'proxy', name='proxy'),
)