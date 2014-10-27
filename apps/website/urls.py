from apps.assets.models import Page
from apps.light.utils import get_store_from_request

from django.conf.urls import patterns, url
from django.http import HttpResponseRedirect

def redirect_to_main(request, path):
    redirect_url = 'http://www.secondfunnel.com' + request.path

    store = get_store_from_request(request)

    if store:
        pages = store.pages.all()
        if pages.count():
            page = pages[0]
            redirect_url = '/%s' % page.url_slug

    return HttpResponseRedirect(redirect_url)

urlpatterns = \
    patterns(
        'apps.website.urls',
        url(r'^(.*)$', redirect_to_main, name='website-index'),
    )
