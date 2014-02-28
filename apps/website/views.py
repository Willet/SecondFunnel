from django.http.response import Http404
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from django.http import HttpResponse

from apps.api.decorators import request_methods
from apps.assets.models import Page

import scripts.generate_rss_feed as rss_feed

@never_cache
@csrf_exempt
@request_methods('GET')
def get_rss_feed(request, feed_name, page_id=0, page_slug=None, **kwargs):
    feed_link = 'http://' + str(request.META['HTTP_HOST']) + '/'
    if page_slug:
        feed_link += str(page_slug) + '/' + str(feed_name)
        page = Page.objects.get(url_slug=page_slug)
    elif page_id:
        feed_link += str(page_id) + '/' + str(feed_name)
        page = Page.objects.get(old_id=page_id)
    else:
        raise Http404("Feed not found")
    feed = rss_feed.main(page, feed_name=feed_name, feed_link=feed_link)
    return HttpResponse(feed, content_type='application/rss+xml')