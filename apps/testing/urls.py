from django.conf.urls import patterns, url
from django.conf import settings


urlpatterns = patterns('apps.testing.views',
    url('^results/$', 'test_results', name='test-results'),
    url('^results/update/.*$', 'fire_test', name='fire-test'),
)
