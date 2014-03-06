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
from apps.contentgraph.views import get_product
from apps.intentrank.views import get_results


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
    except (TypeError, ValueError) as err:
        return default_value, False


def render_campaign(store_id, page_id, request):
    """Generates the HTML page for a standard pinpoint product page.

    Related products are populated statically only if a request object
    is provided.
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

    # these 4 lines will trigger ValueErrors if remote JSON is invalid.
    # page_data = get_page(store_id=store_id, page_id=page_id, as_dict=True)
    # store_data = get_store(store_id=store_id, as_dict=True)

    page = get_object_or_404(Page, old_id=page_id)
    store = get_object_or_404(Store, old_id=store_id)

    ir_base_url = settings.INTENTRANK_BASE_URL + '/intentrank'

    # get the featured product from our DB.
    try:
        # product = content_block.data.product
        # based on Neal's description, this is what it will eventually be
        product = get_product(page.get('featured-product-id')) or\
            get_product(page.get('product-ids', [0])[0])
    except:
        # this is okay
        product = None

    # get backup results
    # ir_id = page.get('intentrank_id') or page_data.get('id')
    # feed = Page.objects.get(old_id=ir_id).feed
    feed = page.feed
    backup_results = get_results(feed=feed, results=20)

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
        "social_buttons": page.social_buttons or \
                          store.get('social-buttons', ''),
        "column_width": page.get('column-width',
                        store.get('column-width', '')),
        "enable_tracking": page.get('enable-tracking', "true"),  # jsbool
        "pub_date": datetime.now(),
        "legal_copy": page.get('legalCopy', ''),
        "mobile_hero_image": page.mobile_hero_image,
        "desktop_hero_image": page.desktop_hero_image,
        "ir_base_url": ir_base_url,
        "ga_account_number": settings.GOOGLE_ANALYTICS_PROPERTY,
        "url": page.get('url', '')
    }

    context = RequestContext(request, attributes)

    # grab the theme url, and then grab the remote file
    # theme_url = page.get('theme') or store.get('theme')
    # if not theme_url:
    #     raise ValueError('page has no theme when campaign manager saved it')

    # page_str, _ = read_remote_file(theme_url)
    page_str = page.theme.load_theme()

    # Replace necessary tags
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
        page_str = regex.sub(repl, page_str)
    except UnicodeDecodeError:
        page_str = regex.sub(repl, page_str.decode('utf-8'))

    # Page content
    page = Template(page_str)

    # Render response
    rendered_page = page.render(context)
    if isinstance(rendered_page, unicode):
        # TODO: Doesn't make sense but is required; why?
        rendered_page = rendered_page.encode('utf-8')

    #noinspection PyArgumentList
    rendered_page = unicode(rendered_page, 'utf-8')

    return rendered_page
