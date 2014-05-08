import gzip
import json
import StringIO
import urllib2

from datetime import datetime
from os import path

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template import RequestContext, Template
from django.utils.safestring import mark_safe

from apps.assets.models import Page, Store


def read_a_file(file_name, default_value=''):
    """just a file opener with a catch."""
    try:
        with open(path.abspath(file_name)) as f:
            return f.read()
    except (IOError, TypeError):
        return default_value


def read_remote_file(url, default_value=''):
    """
    Url opener that reads a url and gets the content body.
    Returns a tuple response where the first item is the data and the
    second is whether the response was gzipped or not.
    """
    try:
        request = urllib2.Request(url)
        request.add_header('Accept-encoding', 'gzip')
        # in case Python-urllib/2.6 would be rejected
        request.add_header('User-agent', 'Mozilla/5.0')
        response = urllib2.urlopen(request)

        if not 200 <= int(response.getcode()) <= 300:
            return default_value, False

        if response.info().get('Content-Encoding') == 'gzip':
            buf = StringIO.StringIO(response.read())
            zfile = gzip.GzipFile(fileobj=buf)
            content = zfile.read()
            zfile.close()
            return content, True

        content = response.read()
        return content, False
    except (TypeError, ValueError, urllib2.HTTPError) as err:
        return default_value, False

def get_store_from_request(request):
    """
    Returns the store pointed to by the request host if it exists.
    Requests forwarded from CloudFront set the HTTP_ORIGIN header
    to the original host.
    """
    if request.META.get('HTTP_USER_AGENT', '') == settings.CLOUDFRONT_USER_AGENT:
        current_url = request.META.get('HTTP_ORIGIN',
                                       request.META.get('HTTP_HOST', ''))
    else:
        current_url = 'http://%s/' % request.get_host()

    try:
        store = Store.objects.get(public_base_url=current_url)
    except Store.DoesNotExist:
        store = None

    return store


def render_campaign(page_id, request, store_id=0):
    """Generates the HTML page for a standard pinpoint product page.

    Backup products are populated statically only if a request object
    is provided.

    :param store_id: optional, legacy, unused
    """
    def json_postprocessor(product_dict):
        """given a product dict, output a product string that can be printed
        with the "|safe" filter.
        """
        if not product_dict:
            return 'null'

        # process tagged_products field, which is a list of products
        if product_dict.get('tagged-products', False):
            rel_products = []
            for rel_product in product_dict['tagged-products']:
                rel_products.append(json.loads(json_postprocessor(rel_product)))
            product_dict['tagged-products'] = rel_products

        escaped_product_dict = {}
        for key in product_dict:
            if isinstance(product_dict[key], (str, basestring)):
                escaped_product_dict[key] = product_dict[key]\
                    .replace('\r', r'\r')\
                    .replace('\n', r'\n')\
                    .replace('"', r'\"')
            else:
                escaped_product_dict[key] = product_dict[key]

        return mark_safe(json.dumps(escaped_product_dict))

    # grab required assets
    page = get_object_or_404(Page, id=page_id)
    page_template = page.theme.load_theme()
    store = page.store
    product = None  # no featured product / STL functionality in place

    ir_base_url = '/intentrank'

    # get backup results
    # backup_results = get_results(feed=feed, results=20)
    backup_results = []  # results are now fetched by client

    if settings.ENVIRONMENT == 'dev' and page.get('ir_base_url'):
        # override the ir_base_url attribute on CG page objects
        # (because you can't test local IR like this)
        setattr(page, 'ir_base_url', '')

    algorithm = request.GET.get('algorithm', page.feed.feed_algorithm or 'generic')
    if request.GET.get('popular', None) == '':
        algorithm = 'popular'

    tests = []
    if page.get('tests'):
        tests = json.dumps(page.get('tests'))

    attributes = {
        "session_id": request.session.session_key,
        "campaign": page,
        "store": store,
        "columns": range(4),
        "preview": False,  # TODO: was this need to fix: not page.live,
        "product": json_postprocessor(product),
        "initial_results": [],  # JS now fetches its own initial results
        "backup_results": map(json_postprocessor, backup_results),
        "social_buttons": page.social_buttons or store.get('social-buttons', ''),
        "conditional_social_buttons": json.dumps(page.get('conditional_social_buttons', {})),
        "column_width": page.column_width or store.get('column-width', ''),
        "enable_tracking": page.enable_tracking,  # jsbool
        # apparently {{ campaign.image_tile_wide|default:0.5 }} is too confusing for django
        "image_tile_wide": page.image_tile_wide,
        "pub_date": datetime.now().isoformat(),
        "legal_copy": page.legal_copy,
        "mobile_hero_image": page.mobile_hero_image,
        "desktop_hero_image": page.desktop_hero_image,
        "ir_base_url": ir_base_url,
        "ga_account_number": settings.GOOGLE_ANALYTICS_PROPERTY,
        "keen_io": settings.KEEN_CONFIG,
        "url": page.get('url', ''),
        "algorithm": algorithm,
        "environment": settings.ENVIRONMENT,
        "tests": tests
    }

    context = RequestContext(request, attributes)

    # Page content
    page = Template(page_template)

    # Render response
    return page.render(context)
