from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.api.decorators import request_methods, check_login
from apps.assets.models import Product, ProductImage
from apps.intentrank.utils import returns_json, returns_cg_json


@request_methods('GET', 'POST', 'PATCH', 'DELETE')
@check_login
@never_cache
@csrf_exempt
@returns_cg_json
def product(request, product_id=0):
    """Implements the following API patterns:

    GET /product
    GET /product/id
    POST /product
    PATCH /product/id
    DELETE /product/id
    """

    if request.method == 'GET':
        if product_id:
            product = get_object_or_404(Product, old_id=product_id)
            return make_cg_product_json(product)
        else:
            return [make_cg_product_json(product)
                    for product in Product.objects.all()]


def make_cg_product_json(product):
    """returns {dict} product in CG json format"""
    return {
        "available": product.attributes.get('available', False),
        "sku": product.sku,
        "default-image": make_cg_image_json(product.default_image),
        # "rescrape": "false",
        "description": "Short sleeves. Crewneck. Screen-printed graphic at front.\nTumble Dry Low Only Non-Chlorine Bleach When Needed Cool Iron On Reverse Do Not Iron On Print",
        "tile-configs": [],
        "image-ids": [i.old_id for i in product.product_images.all()],
        "url": product.url,
        "price": product.price,
        "created": product.created_at,
        "default-image-id": product.default_image_id,
        "last-modified": product.updated_at,
        "last-scraped": product.last_scraped_at,
        "images": [make_cg_image_json(i) for i in product.product_images.all()],
        "product-set": "live",
        "store-id": product.store_id,
        "id": product.old_id,
        "name": product.name,
    }


def make_cg_image_json(image):
    """"""
    return {
        "is-content": "false" if image.__class__ is ProductImage else 'true',
        # "hash": image.hash,
        "tagged-products": [getattr(image, 'product_id')],
        "format": image.file_type,
        "url": image.url,
        "image-sizes": image.attributes.get('sizes'),
        "created": image.created_at,
        "last-modified": image.updated_at,
        "original-url": image.original_url,
        "source": getattr(image, 'source', "image"),
        "dominant-colour": image.dominant_color,
        "store-id": getattr(image, 'store_id', -1),
        "type": "image",
        "id": image.old_id,
    }
