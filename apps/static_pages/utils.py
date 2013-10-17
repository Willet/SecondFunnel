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

from apps.assets.models import Store
from apps.contentgraph.models import get_contentgraph_data
from apps.contentgraph.views import get_page, get_product, get_store
from apps.pinpoint.models import Campaign
from apps.static_pages.models import StaticLog


def save_static_log(object_class, object_id, key):
    # object_type = ContentType.objects.get_for_model(object_class)
    log_record = StaticLog(
        # content_type=object_type,
        object_id=object_id,
        key=key)
    log_record.save()


def remove_static_log(object_class, object_id, key):
    # object_type = ContentType.objects.get_for_model(object_class)
    log_records = StaticLog.objects.filter(
        # content_type=object_type,
        object_id=object_id,
        key=key).delete()


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


def render_campaign(store_id, campaign_id, request, get_seeds_func=None):
    """Generates the HTML page for a standard pinpoint product page.

    Related products are populated statically only if a request object
    is provided.
    """

    def repl(match):
        """Returns a replaced tag content for a tag, or
        the original tag if we have no data for that tag.
        """
        match_str = match.group(1)  # just the field: e.g. 'desktop_content'

        if sub_values.has_key(match_str):
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

    # these 4 lines will trigger ValueErrors if remote JSON is invalid.
    campaign_data = get_page(store_id=store_id, page_id=campaign_id, as_dict=True)
    campaign = Campaign.from_json(campaign_data)
    store_data = get_store(store_id=store_id, as_dict=True)
    store = Store.from_json(store_data)

    # get the featured product from our DB.
    try:
        # product = content_block.data.product
        # based on Neal's description, this is what it will eventually be
        product = get_product(campaign_data.get('featured-product-id')) or\
                  get_product(campaign_data.get('product-ids', [0])[0])
    except:
        # TODO: is this okay?
        product = None

    campaign.description = campaign_data.get('featured_product_description')
    campaign.template = slugify(campaign_data.get('template', 'hero'))  # TODO: hero? hero-image?

    ir_base_url = settings.INTENTRANK_BASE_URL + '/intentrank'

    # "borrow" IR for results
    initial_results = []
    cookie = ''
    try:
        # make IR request without cookie.
        initial_results, cookie = get_seeds_func(
            request,
            store_slug=store_data.get('slug'),
            campaign=campaign_data.get('intentrank_id') or campaign.id,
            base_url=ir_base_url, results=4, raw=True)
    except:  # all exceptions
        pass

    try:
        # make IR request with cookie. (if there is one)
        backup_results, cookie = get_seeds_func(
            request,
            store_slug=store_data.get('slug'),
            campaign=campaign_data.get('intentrank_id') or campaign.id,
            base_url=ir_base_url, results=100, raw=True, cookie=cookie)
    except (TypeError, ValueError):
        # (get_seeds_func is None and you ran it, IR offline)
        backup_results, cookie = ([], '')

    if not initial_results:
        # if there are backup results, serve the first 4.
        initial_results = backup_results[:4]

    attributes = {
        "campaign": campaign,
        "store": store,
        "columns": range(4),
        "preview": not campaign.live,
        "product": json_postprocessor(product),
        "initial_results": map(json_postprocessor, initial_results),
        "backup_results": map(json_postprocessor, backup_results),
        "pub_date": datetime.now(),
        "ir_base_url": ir_base_url,
        "ga_account_number": settings.GOOGLE_ANALYTICS_PROPERTY,
    }

    context = RequestContext(request, attributes)

    # theme is a temporary StoreTheme object
    theme = campaign_data.get('theme')
    if not theme:
        raise ValueError('campaign has no theme when campaign manager saved it')

    # check if the theme is actually a contentgraph resource
    try:
        theme_url = theme.page
        # 'template' is a key proposed by alex
        page_str = get_contentgraph_data(theme_url)['template']['results']
    except (TypeError, ValueError):
        page_str = theme.page  # it's fine, this theme is a string

    # Replace necessary tags
    sub_values = defaultdict(list)
    regex = re.compile("\{\{\s*(\w+)\s*\}\}")

    # replace our own "django-style" tags before django templating touches them
    for field, details in theme.CUSTOM_FIELDS.iteritems():
        # field: e.g. 'desktop_content'
        # details: e.g. {'values': ['pinpoint/campaign_config.html',
        #                           'pinpoint/default_templates.html'],
        #                'type': 'template'}
        field_type = details.get('type')
        values = details.get('values')

        for value in values:  # list of file names or templates

            if field_type == "template":
                result = loader.get_template(value)
            elif field_type == "theme":
                result = getattr(theme, value)
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

    page_str = regex.sub(repl, page_str)

    # Page content
    page = Template(page_str)

    # Render response
    rendered_page = page.render(context)
    if isinstance(rendered_page, unicode):
        # TODO: Doesn't make sense but is required; why?
        rendered_page = rendered_page.encode('utf-8')

    rendered_page = unicode(rendered_page, 'utf-8')

    return rendered_page