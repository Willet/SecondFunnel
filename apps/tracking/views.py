from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import never_cache

TRANSPARENT_1_PIXEL_GIF = "\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00" \
                          "\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00" \
                          "\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00" \
                          "\x00\x02\x02\x44\x01\x00\x3b"


@never_cache
def pixel(request):
    """This is a cookie function. Cookies the user for
    30s ~ 30 mins (see config), or extends tracking time if a request
    is made before the previous cookie expires.
    """
    response = HttpResponse(TRANSPARENT_1_PIXEL_GIF, content_type='image/gif')
    response.set_cookie(
        'visited',
        'true',
        max_age=settings.TRACKING_COOKIE_AGE,
        domain=settings.TRACKING_COOKIE_DOMAIN
    )
    return response


@never_cache
def tracking(request, tracking_id, dev=False):
    response = render_to_response(
        'tracking.js',
        {
            'tracker': tracking_id,
            'dev': dev
        },
        context_instance=RequestContext(request),
        content_type='application/javascript')
    return response


@never_cache
def conversion(request):
    """Loads the clickmeter conversion script."""
    nastygal_clickmeter_conversion_id = '271C54CB40964B26BD0593C4E24EF1C3'
    clickmeter_conversion_id = request.GET.get('id', nastygal_clickmeter_conversion_id)

    response = render_to_response(
        'tracking/js/conversion.js',
        {
            'clickmeter_conversion_id': clickmeter_conversion_id,
        },
        content_type='application/javascript')
    return response


@never_cache
def conversion_loader(request):
    """Loads the clickmeter conversion script loader script."""
    nastygal_clickmeter_conversion_id = '271C54CB40964B26BD0593C4E24EF1C3'
    clickmeter_conversion_id = request.GET.get('id', nastygal_clickmeter_conversion_id)

    response = render_to_response(
        'tracking/js/conversion-loader.js',
        {
            'clickmeter_conversion_id': clickmeter_conversion_id,
        },
        content_type='application/javascript')
    return response
