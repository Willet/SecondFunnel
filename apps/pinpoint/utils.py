import gzip
import json
import re
import StringIO
import urllib2

from collections import defaultdict
from datetime import datetime
from os import path

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template import RequestContext, loader, Template
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe

from apps.assets.models import Theme, Page, Store
from secondfunnel.errors import deprecated


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

        # process related_products field, which is a list of products
        if product_dict.get('related-products', False):
            rel_products = []
            for rel_product in product_dict['related-products']:
                rel_products.append(json.loads(json_postprocessor(rel_product)))
            product_dict['related-products'] = rel_products

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
    page = get_object_or_404(Page, old_id=page_id)
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

    attributes = {
        "campaign": page,
        "store": store,
        "columns": range(4),
        "preview": False,  # TODO: was this need to fix: not page.live,
        "product": json_postprocessor(product),
        "initial_results": [],  # JS now fetches its own initial results
        "backup_results": map(json_postprocessor, backup_results),
        "social_buttons": page.social_buttons or store.get('social-buttons', ''),
        "column_width": page.column_width or store.get('column-width', ''),
        "enable_tracking": page.enable_tracking,  # jsbool
        # apparently {{ campaign.image_tile_wide|default:0.5 }} is too confusing for django
        "image_tile_wide": page.image_tile_wide,
        "pub_date": datetime.now(),
        "legal_copy": page.legal_copy,
        "mobile_hero_image": page.mobile_hero_image,
        "desktop_hero_image": page.desktop_hero_image,
        "ir_base_url": ir_base_url,
        "ga_account_number": settings.GOOGLE_ANALYTICS_PROPERTY,
        "url": page.get('url', ''),
        "related_to_tile": request.GET.get('related', ''),
        "algorithm": request.GET.get('algorithm', page.feed.feed_algorithm or 'generic'),
        "environment": settings.ENVIRONMENT,
    }

    context = RequestContext(request, attributes)

    # Replace tags only if present
    if page_template.find(r'{{ body_content }}') > -1:
        page_template = replace_legacy_tags(page_template, context)

    # Page content
    page = Template(page_template)

    # Render response
    return page.render(context)


@deprecated
def replace_legacy_tags(page_template, context):
    """For themes that still use Theme.CUSTOM_FIELDS, replace run this extra
    replacement algorithm.
    """
    def repl(match):
        """Returns a replaced tag content for a tag, or
        the original tag if we have no data for that tag.
        """
        match_str = match.group(1)  # just the field: e.g. 'desktop_content'

        if match_str in sub_values:
            return ''.join(sub_values[match_str])
        else:
            return match.group(0)  # leave unchanged

    sub_values = defaultdict(list)
    regex = re.compile("\{\{\s*(\w+)\s*\}\}")

    # replace our own "django-style" tags before django templating touches them
    for tag, template in Theme.CUSTOM_FIELDS.iteritems():
        result = loader.get_template(template)

        if isinstance(result, Template):
            result = result.render(context)
        else:
            result = result.encode('unicode-escape')

        try:
            sub_values[tag].append(result.decode("unicode_escape"))
        except UnicodeDecodeError:  # who knows
            sub_values[tag].append(result)

    try:
        page_template = regex.sub(repl, page_template)
    except UnicodeDecodeError:
        page_template = regex.sub(repl, page_template.decode('utf-8'))

    return page_template
