from django.conf.urls import patterns, url

urlpatterns = patterns('apps.assets.views',
    url(r'^importer/(?P<store_id>\d+)/(\w+)/?$', 'import_from_cg',
        name='import-from-cg'),
)
