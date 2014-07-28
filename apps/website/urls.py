from django.conf.urls import patterns, url
from django.http import HttpResponsePermanentRedirect


def redirect_to_main(request, path):
    return HttpResponsePermanentRedirect('http://www.secondfunnel.com' + request.path)

urlpatterns = \
    patterns(
        'apps.website.urls',
        url(r'^(.*)$', redirect_to_main, name='website-index'),
    )
