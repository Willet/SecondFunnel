from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.api.decorators import request_methods, check_login
from apps.assets.models import Product
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
    def make_cg_product_json(product):
        """returns {dict} product in CG json format"""
        return {
            "default-image-id": "14291",
            "last-modified": "1394775877605",
            "rescrape": "false",
            "product-set": "live",
            "image-ids": [
                "14292",
                "14291"
            ],
            "available": "true",
            "sku": "959472",
            "url": "http://www.gap.com/browse/product.do?pid\u003d959472",
            "id": "3045",
            "price": "$88.00",
            "created": "1394092849261",
            "description": "Long sleeves with button cuffs. Notched lapel. Double-button front. Welt pocket at chest, patch pockets at sides. Seam details throughout. Allover multi-stripes.",
            "name": "Classic stripe blazer",
            "store-id": "38",
            "last-scraped": "1394775827025"
        }

    if request.method == 'GET':
        if product_id:
            product = get_object_or_404(Product, old_id=product_id)
            return make_cg_product_json(product)
        else:
            return [make_cg_product_json(product)
                    for product in Product.objects.all()]
