import json
from django.utils.safestring import mark_safe
import re

from collections import defaultdict
from datetime import datetime

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.template import RequestContext, loader, Template
from django.template.defaultfilters import slugify
from django.test import RequestFactory
from django.utils.importlib import import_module
from apps.assets.models import Feed, Page, Store, Product

# from apps.contentgraph.views import get_page, get_product, get_store
from apps.intentrank.views import get_results
from apps.pinpoint.utils import read_remote_file
from apps.pinpoint.models import StoreTheme


def get_bucket_name(bucket_name):
    """
    Generates a bucket name based on current environment.
    """

    if settings.ENVIRONMENT in ["test", "dev"]:
        str_format = '{0}-{1}.secondfunnel.com'
        return str_format.format(settings.ENVIRONMENT, bucket_name)

    elif settings.ENVIRONMENT == "production":
        str_format = '{0}.secondfunnel.com'
        return str_format.format(bucket_name)

    else:
        raise Exception("Unknown ENVIRONMENT name: {0}".format(
            settings.ENVIRONMENT))


def create_dummy_request():
    # Monkeypatch request
    # https://code.djangoproject.com/ticket/15736?cversion=0&cnum_hist=1
    def request(self, **request):
        "Construct a generic request object."
        req = WSGIRequest(self._base_environ(**request))
        req.session = self._session()
        return req

    def _session(self):
        """
        Obtains the current session variables.
        """
        if 'django.contrib.sessions' in settings.INSTALLED_APPS:
            engine = import_module(settings.SESSION_ENGINE)
            cookie = self.cookies.get(settings.SESSION_COOKIE_NAME, None)
            if cookie:
                return engine.SessionStore(cookie.value)
        return {}

    RequestFactory._session = _session
    RequestFactory.request = request

    return RequestFactory().get('/')


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
        if product_dict:
            if not product_dict.get('content-id', False):
                product_dict['content-id'] = product_dict.get('id', -1)

            if not product_dict.get('db-id', False):
                product_dict['db-id'] = product_dict.get(
                    'db_id', product_dict.get('db-id', None))

            if not product_dict.get('title', False):
                product_dict['title'] = product_dict.get('name', '')

            if not product_dict.get('template', False):
                product_dict['template'] = 'product'

            if not product_dict.get('provider', False):
                product_dict['provider'] = 'youtube'

            # process related_products field, which is a list of products
            if product_dict.get('related_products', False):
                rel_products = []
                for rel_product in product_dict['related_products']:
                    rel_products.append(json.loads(json_postprocessor(rel_product)))
                product_dict['related_products'] = rel_products

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
        else:
            return 'null'

    page = Page.objects.get(id=page_id)
    store_data = Store.objects.get(id=store_id)
    store = store_data

    # get the featured product from our DB.
    try:
        # product = content_block.data.product
        # based on Neal's description, this is what it will eventually be
        product = Product.objects.get(page.get('featured-product-id')) or\
            Product.objects.get(page.get('product-ids', [0])[0])
    except:
        # TODO: is this okay?
        product = None

    page.description = getattr(page, 'shareText', getattr(page, 'featured-product-description', ''))
    if not page.template:
        page.template = 'hero'
    page.image_tile_wide = getattr(page, 'imageTileWide', 0.5)

    ir_base_url = settings.INTENTRANK_BASE_URL + '/intentrank'

    # "borrow" IR for results
    feed = Feed.objects.get(id=getattr(page, 'intentrank_id',getattr(page, 'id', 0)))
    initial_results = get_results(feed=feed, results=4, algorithm='first')
    backup_results = get_results(feed=feed, results=100)

    if not initial_results:
        # if there are backup results, serve the first 4.
        initial_results = backup_results[:4]

    attributes = {
        "campaign": page,
        "store": store,
        "columns": range(4),
        "preview": False,  # TODO: was this need to fix: not page.live,
        "product": json_postprocessor(product),
        "initial_results": map(json_postprocessor, initial_results),
        "backup_results": map(json_postprocessor, backup_results),
        "social_buttons": getattr(page, 'social-buttons',
                                  getattr(store, 'social-buttons', '')),
        "column_width": getattr(page, 'column-width',
                                getattr(store, 'column-width', '')),
        "enable_tracking": getattr(page, 'enable-tracking', "true"),  # jsbool
        "pub_date": datetime.now(),
        "legal_copy": getattr(page, 'legalCopy', ''),
        "mobile_hero_image": getattr(page, 'heroImageMobile', ''),
        "desktop_hero_image": getattr(page, 'heroImageDesktop', ''),
        "ir_base_url": ir_base_url,
        "ga_account_number": settings.GOOGLE_ANALYTICS_PROPERTY,
        "url": getattr(page, 'url', '')
    }

    context = RequestContext(request, attributes)

    # grab the theme url, and then grab the remote file
    theme_url = page.theme.template or store.default_theme.template
    if not theme_url:
        raise ValueError('page has no theme when campaign manager saved it')

    page_str = read_remote_file(theme_url)

    # Replace necessary tags
    sub_values = defaultdict(list)
    regex = re.compile("\{\{\s*(\w+)\s*\}\}")

    # replace our own "django-style" tags before django templating touches them
    for field, details in StoreTheme.CUSTOM_FIELDS.iteritems():
        # field: e.g. 'desktop_content'
        # details: e.g. {'values': ['pinpoint/campaign_config.html',
        #                           'pinpoint/default_templates.html'],
        #                'type': 'template'}
        field_type = details.get('type')
        values = details.get('values')

        for value in values:  # list of file names or templates

            if field_type == "template":
                result = loader.get_template(value)
            else:
                continue

            if isinstance(result, Template):
                result = result.render(context)
            else:
                result = result.encode('unicode-escape')

            try:
                sub_values[field].append(result.decode("unicode_escape"))
            except UnicodeDecodeError:  # who knows
                sub_values[field].append(result)

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
