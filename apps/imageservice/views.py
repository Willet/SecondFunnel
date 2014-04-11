import json

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from apps.imageservice.tasks import process_image
from apps.imageservice.utils import create_image_path
from apps.assets.models import ProductImage, Image, Product, Store
from apps.intentrank.utils import ajax_jsonp


def has_image_key(fn):
    """Decorator that ensures a file or url was passed."""
    def wrapped_function(request, *args, **kwargs):
        """Wrapper that calls the view."""
        img, data = None, {}

        try:
            if len(request.FILES.keys()) > 0:
                files = request.FILES.values()
                data = []
                for f in files:
                    data.append(fn(request, f, *args, **kwargs))
                data = data[0] if len(data) == 1 else data
            elif request.POST.get('url', None):
                data = fn(request, request.POST.get('url'), *args, **kwargs)
            return HttpResponse(json.dumps(data), content_type="application/json", status=200)

        except Exception as e:
            return HttpResponse(json.dumps({
                'error': {
                    'message': str(e),
                },
                'success': False
            }), content_type="application/json", status=400)

    return wrapped_function


@csrf_exempt
@login_required
@require_http_methods(["POST"])
@has_image_key
def create(request, img):
    """
    Processes an image and uploads it to the specified MEDIA_URL.

    @param request: HttpRequest
    @param img: str
    @return: HttpResponse
    """
    path = settings.MEDIA_URL
    data = process_image(img, path)

    return ajax_jsonp({'url': data['url']})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
@has_image_key
def create_image(request, img, store_id, source):
    """
    Consumes a request object with a passed file and delegates it to the
    image service for processing, assigning it to a store.

    @param request: HttpRequest object
    @param img: str
    @param store_id: The store id
    @param source: The source of the image
    @return: HttpResponse
    """
    path = create_image_path(store_id, source)
    data = process_image(img, path)
    store = Store.objects.get(pk=store_id)

    # Get the last old id to use for this object
    image = Image(original_url=request.POST.get('url'), attributes=data['sizes'],
        dominant_color=data['dominant-color'], url=data['url'], store=store,
        source=source, file_type=data['format'])

    image.save()
    return image.to_json()


@csrf_exempt
@login_required
@require_http_methods(["POST"])
@has_image_key
def create_product_image(request, img, store_id, product_id, source):
    """
    Consumes a request object with a passed file and delegates it to the
    imageservice for processing and assigns it to a product.

    @param request: HttpRequest object
    @param img: str
    @param store_id: The store id
    @param product_id: The product id
    @param source:
    @return: HttpResponse
    """
    path = create_image_path(store_id, source)
    data = process_image(img, path)
    product = Product.objects.get(pk=product_id)

    # Get the last old id to use for this object
    # TODO: This will eventually be phased out
    image = ProductImage(product=product, original_url=request.POST['url'],
        attributes=data['sizes'], dominant_color=data['dominant-color'],
        url=data['url'], file_type=data['format'])

    image.save()
    return image.to_json()
