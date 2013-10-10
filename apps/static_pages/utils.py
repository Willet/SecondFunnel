import json
import re

from collections import defaultdict
from datetime import datetime

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.handlers.wsgi import WSGIRequest
from django.template import RequestContext, loader, Template
from django.template.defaultfilters import slugify
from django.test import RequestFactory
from django.utils.importlib import import_module

from apps.assets.models import Store, Product
from apps.contentgraph.views import get_page
from apps.pinpoint.models import StoreTheme, Campaign
from apps.static_pages.models import StaticLog


def save_static_log(object_class, object_id, key):
    object_type = ContentType.objects.get_for_model(object_class)
    log_record = StaticLog(
        content_type=object_type, object_id=object_id, key=key)
    log_record.save()


def remove_static_log(object_class, object_id, key):
    object_type = ContentType.objects.get_for_model(object_class)
    log_records = StaticLog.objects.filter(
        content_type=object_type, object_id=object_id, key=key).delete()


def bucket_exists_or_pending(store):
    store_type = ContentType.objects.get_for_model(Store)

    log_records = StaticLog.objects.filter(
            content_type=store_type, object_id=store.id)

    return len(log_records) > 1


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

    campaign = None
    campaign_data = {}
    try:
        campaign_cg = get_page(store_id=store_id, page_id=campaign_id)
        campaign_data = campaign_cg.json(False)
        campaign = Campaign.from_json(campaign_data)
    except ValueError:
        raise  # json error

    # TODO: Content blocks don't make as much sense now; when to clean up?
    # TODO: If we keep content blocks, should this be a method?
    # Assume only one content block
    content_block = None
    try:
        content_block = campaign.content_blocks.all()[0]
    except AttributeError:  # transition complete
        content_block = campaign.content_block
    finally:
        if not content_block:
            content_block = ''


    try:
        # product = content_block.data.product
        product = Product.objects.get(pk=campaign_data.get('featured_product_id'))
    except:
        # TODO: is this okay?
        product = None

    # campaign.description = (content_block.data.description or product.description).encode('unicode_escape')
    campaign.description = campaign_data.get('featured_product_description')
    campaign.template = slugify(campaign_data.get('template', 'hero'))  # TODO: hero? hero-image?

    if settings.DEBUG:
        # If in debug mode, or we otherwise need to use the old proxy
        base_url = settings.WEBSITE_BASE_URL + '/intentrank'
    else:
        base_url = settings.INTENTRANK_BASE_URL + '/intentrank'

    # "borrow" IR for results
    if get_seeds_func:
        backup_results = get_seeds_func(
            request,
            # store=campaign.store.slug,
            store=campaign_data.get('store_slug'),
            # campaign=campaign.default_intentrank_id or campaign.id,
            campaign=campaign_data.get('intentrank_id') or campaign.id,
            base_url=base_url, results=100, raw=True)
    else:
        backup_results = []

    attributes = {
        "campaign": campaign,
        "columns": range(4),
        "preview": not campaign.live,
        "product": product,
        "backup_results": backup_results,
        "pub_date": datetime.now(),
        "base_url": base_url,
        "ga_account_number": settings.GOOGLE_ANALYTICS_PROPERTY,
    }

    context = RequestContext(request, attributes)

    try:
        # theme = campaign.get_theme()
        theme_data = campaign_data.get('theme') or campaign.get_theme()  # likely transition

        if not theme_data:
            raise ValueError('campaign has no theme when campaign manager saved it')

        # page_str = theme.page
        theme = StoreTheme(theme_data)  # likely transition
    except ValueError:
        raise  # TODO: otherwise...?

    page_str = theme.page

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