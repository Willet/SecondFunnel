import json
import random

from urllib import urlencode
from random import randrange

from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponse
from django.template import Context, loader, TemplateDoesNotExist
import httplib2
from mock import MagicMock

from apps.assets.models import Product, Store

from apps.intentrank.utils import random_products, ajax_jsonp

from apps.pinpoint.models import IntentRankCampaign

SUCCESS = 200
FAIL400 = 400
SUCCESS_STATUSES = xrange(SUCCESS, 300)
DEFAULT_RESULTS  = 12
MAX_BLOCKS_BEFORE_VIDEO = 50


def send_intentrank_request(request, url, method='GET', headers=None,
                            http=httplib2.Http):
    """
    Sends a given request to intentrank with the given headers.

    @param request: The request to the django intentrank api.
    @param url: The url to the intentrank service.
    @param method:
    @param headers: The headers for the request to the intentrank service.

    @return: A tuple with a response code and the content that was returned.
    """
    if not headers:
        headers = {}

    cookie = request.session.get('ir-cookie')
    if cookie:
        headers['Cookie'] = cookie

    h = http()
    response, content = h.request(
        url,
        method=method,
        headers=headers,
    )

    if response.get('set-cookie'):
        request.session['ir-cookie'] = response['set-cookie']

    return response, content


def send_request(request, url, method='GET', headers=None):
    """
    Sends a given request to intentrank with the given headers.

    @param request: The request to the django intentrank api.
    @param url: The url to the intentrank service.
    @param method:
    @param headers: The headers for the request to the intentrank service.

    @return: A tuple with a response code and the content that was returned.
    """
    if not headers:
        headers = {}

    h = httplib2.Http()
    response, content = h.request(
        url,
        method=method,
        headers=headers,
    )

    return response, content


def get_product_json_data(product, products_with_images_only=True):
    """Enforce common product json structures across both
    live and static IR.

    input: Product product
    output: Dict (json object)

    This function raises an exception if products_with_images_only is True,
    but the product has none.

    """
    if not product:
        raise ValueError('Supplied product is not valid.')

    if products_with_images_only and not product.images():
        raise ValueError('Product has no images, but one or more is required.')

    try:
        product_template = loader.get_template(
            'pinpoint/snippets/product_object.js')
        product_context = Context({'product': product})
        return json.loads(product_template.render(product_context))
    except TemplateDoesNotExist:
        if settings.DEBUG: # tell (only) devs if something went wrong.
            raise

    # Product json template is AWOL.
    # Fall back to however we rendered products before
    product_props = product.data(raw=True)
    product_js_obj = {}
    for prop in product_props:
        # where product_prop is ('data-key', 'value')
        product_js_obj[prop] = product_props[prop]
    return product_js_obj


def get_json_data(request, products, campaign_id, seeds=None):
    """returns json equivalent of get_blocks' blocks.

    seeds is a list of product IDs.

    results will be an object {}, not an array [].
    products_with_images_only should be either '0' or '1', please.
    """
    ir_campaign = IntentRankCampaign.objects.get(pk=campaign_id)
    
    campaign = ir_campaign.campaigns.all()[0]
    
    results = []
    products_with_images_only = True
    if request.GET.get('products_with_images_only', '1') == '0':
        products_with_images_only = False

    # products
    for product in products:
        try:
            if not product:
                continue

            product_js_obj = cache.get("product_js_obj-{0}-{1}".format(
                product.id, products_with_images_only))

            if not product_js_obj:
                product_js_obj = get_product_json_data(product=product,
                   products_with_images_only=products_with_images_only)

                cache.set(
                    "product_js_obj-{0}-{1}".format(
                        product.id, products_with_images_only),

                    product_js_obj,

                    # cache for 3 hours
                    60*60*4
                )

            results.append(product_js_obj)
        except ValueError:
            # caused by product image requirement.
            # if that requirement is not met, ignore product.
            continue

    # store-wide external content
    external_content = cache.get('storec-external-content-{0}-{1}'.format(
        campaign.store.id, campaign_id))

    if not external_content:
        external_content = campaign.store.external_content.filter(
            active=True, approved=True)
        if campaign.supports_categories:
            external_content = external_content.filter(categories__id=campaign_id)

        cache.set('storec-external-content-{0}-{1}'.format(
            campaign.store.id, campaign_id),external_content, 60*60*4)

    # content to product ration. e.g., 2 == content to products 2:1
    content_to_products = 1

    need_to_show = int(round(len(results) * content_to_products))

    if len(external_content) > 0 and need_to_show > 0:
        need_to_show = min(need_to_show, len(external_content))

        for item in random.sample(external_content, need_to_show):
            json_content = item.to_json()
            json_content.update({
                'template': item.content_type.name.lower()
            })

            related_products = cache.get('ec-tagged-prods-{0}'.format(item.id))
            if not related_products:
                related_products = item.tagged_products.all()

                cache.set('ec-tagged-prods-{0}'.format(item.id),
                    related_products, 60*60)

            if related_products:
                json_content.update({
                    'related-products': [x.data(raw=True)
                        for x in related_products]
                })

            results.insert(randrange(len(results) + 1), json_content)
            
    return results
        

def get_seeds(request, **kwargs):
    """Gets initial results (products, photos, etc.) to be saved with a page

    kwargs['raw'] also toggles between returning a dictionary
    or an entire HttpResponse.
    """
    # IR uses a cookie previously sent to us as a flag
    cookie = kwargs.get('cookie', '')

    num_results = kwargs.get('results', request.GET.get('results',  DEFAULT_RESULTS))

    # store now needs to be a slug
    store_slug = kwargs.get('store_slug', request.GET.get('store_slug',
                                                          'store_slug'))
    campaign = kwargs.get('campaign', request.GET.get('campaign', '-1'))

    callback = kwargs.get('callback', request.GET.get('callback', 'fn'))
    base_url = kwargs.get('base_url', request.GET.get(
        'base_url',
        settings.INTENTRANK_BASE_URL + '/intentrank'
    ))

    url = '{0}/page/{1}/getresults'.format(base_url, campaign)

    # Add required get parameters
    url += "?results={0}".format(num_results)

    # Fetch results
    try:
        response, content = send_request(request, url,
                                         headers={'Cookie': cookie})
        status = response['status']
        cookie = response.get('set-cookie', '')
        content = unicode(content, 'windows-1252')
        if status >= 400:
            raise ValueError('get_seeds received error')
    except httplib2.HttpLib2Error as e:
        # Don't care what went wrong; do something!
        content = u"{'error': '{0}'}".format(str(e))
        status = 400
    except ValueError:
        raise

    # Since we are sending the request, and we'll get JSONP back
    # we know what the callback will be named
    prefix = '{0}('.format(callback)
    suffix = ');'
    if content.startswith(prefix) and content.endswith(suffix):
        content = content[len(prefix):-len(suffix)]

    # Check results
    try:
        results = json.loads(content)
    except ValueError:
        results = {"error": content}

    if 'error' in results:
        results.update({'url': url})

    # post-processing for django templates: they can't access any attribute
    # with a hyphen in it
    new_results = []
    for result in results:
        new_result = {}
        for attrib in result:
            new_result[attrib] = result[attrib]
            new_result[attrib.replace('-', '_')] = result[attrib]
        new_results.append(new_result)

    if kwargs.get('raw', False):
        return (new_results, cookie)
    else:
        return ajax_jsonp(new_results, callback, status=status)


def update_clickstream(request):
    """
    Tells intentrank what producs have been clicked on.

    @param request: The request.

    @return: A json HttpResonse that is empty or contains an error.  Displays nothing on success.
    """

    callback = request.GET.get('callback', 'fn')

    # Proxy is *mostly* deprecated; always succeed
    return ajax_jsonp([], callback, status=SUCCESS)



def get_results_dev(request, store_slug, campaign, content_id=None, **kwargs):
    """Returns random results for a campaign

    kwargs['raw'] also toggles between returning a dictionary
    or an entire HttpResponse.
    """
    callback = kwargs.get('callback', request.GET.get('callback', 'fn'))

    products = random_products(store_slug, {'results': DEFAULT_RESULTS},
                               id_only=True)
    filtered_products = Product.objects.filter(
        pk__in=products, available=True)
    results = get_json_data(request, filtered_products, campaign)

    if kwargs.get('raw', False):
        return results
    else:
        return ajax_jsonp(results, callback, status=200)
