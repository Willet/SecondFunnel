from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

TRANSPARENT_1_PIXEL_GIF = "\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"

def pixel(request):
    response = HttpResponse(TRANSPARENT_1_PIXEL_GIF, content_type='image/gif')
    response.set_cookie('visited', 'true', max_age=settings.TRACKING_COOKIE_AGE)
    return response

def tracking(request, tracking_id):
    response = render_to_response(
        'tracking.js',
        {'tracker': tracking_id},
        context_instance=RequestContext(request),
        content_type='application/javascript')
    return response