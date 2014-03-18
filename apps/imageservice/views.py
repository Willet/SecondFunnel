from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from apps.imageservice.tasks import process_image
from apps.imageservice.utils import create_image_path
from apps.utils.ajax import ajax_success, ajax_error
from apps.pinpoint.utils import read_remote_file


# The image url parameter fields
IMAGE_KEY_FIELDS = ['file', 'url']


class ParameterException(Exception):
    pass


@csrf_exempt
@require_http_methods(["POST"])
def create(request):
    """
    Processes an image and uploads it to the specified MEDIA_URL.

    @param request: HttpRequest
    @return: HttpResponse
    """
    image_source = None

    try:
        image_source = get_file(request.POST)
    except ParameterException as e:
        return ajax_error({"msg": str(e)})

    path = settings.MEDIA_URL
    data = process_image(image_source)

    return ajax_success({
        'response': data
    })


@csrf_exempt
@require_http_methods(["POST"])
def create_image(request, store_id, source):
    """
    Consumes a request object with a passed file and delegates it to the
    image service for processing, assigning it to a store.

    @param request: HttpRequest object
    @param store_id: The stoer id
    @return: HttpResponse
    """
    image_source = None

    try:
        image_source = get_file(request.POST)
    except ParameterException as e:
        return ajax_error({"msg": str(e)})

    path = create_image_path(store_id, source)
    data = process_image(image_source, path)
    # TODO: Assign to store

    return ajax_success({
        'response': data
    })


@csrf_exempt
@require_http_methods(["POST"])
def create_product_image(request, store_id, product_id, source):
    """
    Consumes a request object with a passed file and delegates it to the
    imageservice for processing and assigns it to a product.

    @param request: HttpRequest object
    @param store_id: The store id
    @param product_id: The product id
    @param source:
    @return: HttpResponse
    """
    image_source = None

    try: # Try to get the file
        image_source = get_file(request.POST)
    except ParameterException as e:
        return ajax_error({'msg': str(e)})

    path = create_image_path(store_id, source)
    data = process_image(image_source, path)
    # TODO: Assign to store product

    return ajax_success({
        'response': data
    })


def get_file(params):
    """
    Determine the passed file from the dictionary of values.

    @param params: dict
    @return: str
    """
    source_file = None

    for key in IMAGE_KEY_FIELDS: # iterate over file params
        val = params.get(key, None)
        if val is not None:
            if source_file is not None:
                raise ParameterException("Too many sources found.  Expected only one.")
            if key == 'url':
                source_file, _ = read_remote_file(val)
            else:
                source_file = val

    # Ensure we have a file
    if source_file is None:
        raise ParameterException("No file passed.")

    return source_file
