from collections import defaultdict
import httplib2
import json

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotAllowed

from apps.api.decorators import check_login
from apps.intentrank.utils import ajax_jsonp


def get_proxy_results(request, url, body=None):
    """small wrapper around all api requests to content graph.

    :returns tuple
    :raises (ValueError, IndexError)
    """
    h = httplib2.Http()
    response, content = h.request(url, method=request.method, body=body,
                                  headers=request.NEW_HEADERS or request.META)

    resp_obj = json.loads(content)
    return (resp_obj['results'], resp_obj['meta'])


@check_login
def proxy_view(request, path):
    """Nick is not a security expert.

    He does, however, recommend we read up security policy to see if using
    CORS is sufficient to prevent against CSRF, because he is having a hard time
    handling that...
    """

    target_url = settings.CONTENTGRAPH_BASE_URL

    url = '%s/%s' % (target_url, path)
    if request.META.get('QUERY_STRING', False):
        url += '?' + request.META['QUERY_STRING']

    h = httplib2.Http()
    response, content = h.request(
        url,
        method=request.method,
        body=request.body or None,
        headers=request.NEW_HEADERS
    )

    return HttpResponse(
        content=content,
        status=response['status'],
        content_type=response['content-type']
    )


@check_login
def get_page_content_by_product(request, store_id, page_id):
    """Returns a multiple lists of product content grouped by
    their product id.
    """
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    product_url = "%s/store/%s/page/%s/product/ids" % (
        settings.CONTENTGRAPH_BASE_URL, store_id, page_id)
    content_url = "%s/store/%s/content?tagged-products=%s"

    results = defaultdict(list)

    product_ids, meta = get_proxy_results(request=request, url=product_url)
    for product_id in product_ids:
        content, _ = get_proxy_results(request=request,
            url=content_url % (settings.CONTENTGRAPH_BASE_URL, store_id,
                               product_id))
        results[u'%s' % product_id].append(content)

    return ajax_jsonp({'results': results,
                       'meta': meta})
