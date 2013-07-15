import json
import random

from random import randrange

from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponse
from django.template import Context, loader, TemplateDoesNotExist
import httplib2

from apps.assets.models import Product, Store

from apps.intentrank.utils import (random_products, VideoCookie,
    video_probability_function, ajax_jsonp)

from apps.pinpoint.models import IntentRankCampaign

SUCCESS = 200
FAIL400 = 400
SUCCESS_STATUSES = xrange(SUCCESS, 300)
DEFAULT_RESULTS  = 12
MAX_BLOCKS_BEFORE_VIDEO = 50


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
        product_template = loader.get_template('pinpoint/snippets/'
                                               'product_object.js')
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

    
    # videos
    video_cookie = request.session.get('pinpoint-video-cookie')
    if not video_cookie:
        video_cookie = request.session['pinpoint-video-cookie'] = VideoCookie()

    videos = cache.get('videos-campaign-{0}'.format(campaign_id))
    if not videos:
        videos = campaign.store.videos.exclude(
            video_id__in=video_cookie.videos_already_shown)

        if campaign.supports_categories:
            videos = videos.filter(categories__id=campaign_id)

        cache.set('videos-campaign-{0}'.format(campaign_id), videos, 60*60*3)

    # if this is the first batch of results, or the random amount is under the
    # curve of the probability function, then add a video
    show_video = random.random() <= video_probability_function(
        video_cookie.blocks_since_last, MAX_BLOCKS_BEFORE_VIDEO)
    if videos.exists() and (video_cookie.is_empty() or show_video):
        video = videos.order_by('?')[0]
        results.append({
            'id': video.video_id,
            'url': 'http://www.youtube.com/watch?v={0}'.format(video.video_id),
            'provider': 'youtube',
            'width': '450',
            'height': '250',
            'autoplay': 0,
            'template': 'youtube'
        })
        video_cookie.add_video(video.video_id)
    else:
        video_cookie.add_blocks(len(results))

    request.session['pinpoint-video-cookie'] = video_cookie

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
    num_results = kwargs.get('results', request.GET.get('results',  DEFAULT_RESULTS))

    store = kwargs.get('store', request.GET.get('store', '-1'))
    campaign = kwargs.get('campaign', request.GET.get('campaign', '-1'))
    callback = kwargs.get('callback', request.GET.get('callback', 'fn'))
    base_url = kwargs.get('base_url', request.GET.get('base_url',
                                                      settings.INTENTRANK_BASE_URL))

    # TODO: How do we specify number of results?
    url = '{0}/store/{1}/page/{2}/getresults'.format(base_url, store, campaign)

    # Fetch results
    try:
        response, content = send_request(request, url)
        status = response.status
    except httplib2.HttpLib2Error:
        # Don't care what went wrong; do something!
        content = "{}"
        status = 400

    # Since we are sending the request, and we'll get JSONP back
    # we know what the callback will be named
    prefix = 'fn('
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

    if kwargs.get('raw', False):
        return results
    else:
        return ajax_jsonp(results, callback, status=status)


def get_results(request, store_id, campaign, content_id=None, **kwargs):
    """Returns random results for a campaign

    kwargs['raw'] also toggles between returning a dictionary
    or an entire HttpResponse.
    """
    callback = kwargs.get('callback', request.GET.get('callback', 'fn'))

    products = random_products(store_id, {'results': DEFAULT_RESULTS},
                               id_only=True)
    filtered_products = Product.objects.filter(
        pk__in=products, available=True).exclude(media=None)
    results = get_json_data(request, filtered_products, campaign)

    if kwargs.get('raw', False):
        return results
    else:
        return ajax_jsonp(results, callback, status=200)


# WARNING: As soon as Neal's service is up and running,
# REMOVE THESE TWO METHODS BELOW
def get_related_content_product(request, id=None):
    if not id:
        raise Exception('No ID')

    product = Product.objects.get(id=id)

    results = []
    result = get_product_json_data(product,
                                   products_with_images_only=False)
    result.update({
        'db-id': product.id
    })

    # Append the product JSON itself
    results.append(result)

    # Need to include related products to duplicate existing functionality
    related_content = product.external_content.filter(active=True, approved=True)
    for content in related_content:
        item = content.to_json()
        item.update({
            'db-id': content.id,
            'template': content.content_type.name.lower(),
            'categories': list(
                content.categories.all().values_list('id', flat=True)
            )
        })

        # Need to include related products to duplicate existing functionality
        related_products = content.tagged_products.all()
        rel_product_results = []
        for rel_product in related_products:
            data = rel_product.data(raw=True)
            data.update({'db-id': rel_product.id})
            rel_product_results.append(data)

        item.update({
            'related-products': rel_product_results
        })

        results.append(item)

    return HttpResponse(json.dumps(results), content_type='application/json')

def get_related_content_store(request, id=None):
    if not id:
        raise Exception('No ID')

    store = Store.objects.get(id=id)

    # Get external content associated with store
    results = []
    related_external_content = store.external_content.filter(active=True, approved=True)
    for content in related_external_content:
        item = content.to_json()
        item.update({
            'db-id': content.id,
            'template': content.content_type.name.lower(),
            'categories': list(
                content.categories.all().values_list('id', flat=True)
            )
        })

        # Need to include related products to duplicate existing functionality
        related_products = content.tagged_products.all()
        rel_product_results = []
        for rel_product in related_products:
            data = rel_product.data(raw=True)
            data.update({'db-id': rel_product.id})
            rel_product_results.append(data)


        item.update({
            'related-products': rel_product_results
        })

        results.append(item)

    # Get Youtube content associated with store
    videos = store.videos.all()
    for video in videos:
        results.append({
            'db-id': video.id,
            'id': video.video_id,
            'url': 'http://www.youtube.com/watch?v={0}'.format(video.video_id),
            'provider': 'youtube',
            'width': '450',
            'height': '250',
            'autoplay': 0,
            'template': 'youtube',
            'categories': list(
                video.categories.all().values_list('id', flat=True)
            )
        })

    return HttpResponse(json.dumps(results), content_type='application/json')
