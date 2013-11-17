from collections import defaultdict
from datetime import datetime
import json
import re
from urlparse import urlparse
from django.conf import settings
from django.core.cache import cache
from django.template import RequestContext, loader, Template
from django.utils.safestring import mark_safe
from apps.contentgraph.views import proxy_product
from apps.intentrank.views import proxy_get_results
from apps.utils.s3 import create_bucket_website_alias, get_bucket_name, upload_to_bucket

ROUTE_53_LOCK_EXPIRE = 60 * 5
ROUTE_53_LOCK = "r53-lock"

ACQUIRE_LOCK = lambda: cache.add(
    ROUTE_53_LOCK, "true", ROUTE_53_LOCK_EXPIRE)
RELEASE_LOCK = lambda: cache.delete(ROUTE_53_LOCK)

def get_or_create_bucket(store):
    # Warning: This code used to rely on Celery in case of failure
    # TODO: Verify that this code works without Celery
    ACQUIRE_LOCK()

    store_url = ''
    if store.get('public-base-url', False):
        url = urlparse(store.get('public-base-url')).hostname
        if url:
            store_url = url

    dns_name = get_bucket_name(store.get('slug'))
    bucket_name = store_url or dns_name

    # check for dev/test prefix. This allows campaign.url from campaign manager
    # to be a full secondfunnel.com url.
    if settings.ENVIRONMENT in ["test", "dev"]:
        if not bucket_name[:len(settings.ENVIRONMENT)] == settings.ENVIRONMENT:
            bucket_name = '{0}-{1}'.format(settings.ENVIRONMENT, bucket_name)

    _, change_status, change_id = create_bucket_website_alias(dns_name, bucket_name)

    RELEASE_LOCK()

def generate_page(request, store, page):
    page_content = render_page(store, page)

    page_url = page.get('url') or page.get('slug') or page.get('id')

    # e.g. "shorts3/index.html"
    s3_path = "{0}/index.html".format(page_url)

    store_url = ''
    # this will err intentionally if a store has no public base url
    url = urlparse(getattr(store, 'public-base-url')).hostname
    if url:
        store_url = url

    dns_name = get_bucket_name(store.slug)
    bucket_name = store_url or dns_name

    # check for dev/test prefix. This allows campaign.url from campaign manager
    # to be a full secondfunnel.com url.
    if settings.ENVIRONMENT in ["test", "dev"]:
        if not bucket_name[:len(settings.ENVIRONMENT)] == settings.ENVIRONMENT:
            bucket_name = '{0}-{1}'.format(settings.ENVIRONMENT, bucket_name)

    bytes_written = upload_to_bucket(
        bucket_name, s3_path, page_content, public=True)

    if bytes_written > 0:
        pass

    # boto claims it didn't write anything to S3
    else:
        pass

    # return some kind of feedback
    return {
        's3_path': s3_path,
        'bucket_name': bucket_name,
        'campaign': page,  # warning: contains store theme
        'store': store,
        'bytes_written': bytes_written,
    }


def render_page(request, store, page):
    request_context = generate_page_variables(request, store, page)

    page_template = generate_page_theme(request_context)

    # Page content
    page = Template(page_template)

    # Render response
    rendered_page = page.render(request_context)
    if isinstance(rendered_page, unicode):
        # TODO: Doesn't make sense but is required; why?
        rendered_page = rendered_page.encode('utf-8')

    rendered_page = unicode(rendered_page, 'utf-8')

    return rendered_page


def generate_page_variables(request, store, page):
    store_id = store.get('id')

    product_id = store.get('featured-product-id') or \
                 store.get('product-ids', [0])[0]

    product_json = proxy_product(request, store_id, product_id)
    product = json.loads(product_json)

    intentrank_base_url = settings.INTENTRANK_BASE_URL + '/intentrank'

    # TODO: Restrict to 4 results
    initial_results_json = proxy_get_results(page.get('id'), raw=True)
    initial_results = json.loads(initial_results_json)

    # TODO: Restrict to 100 results
    backup_results_json = proxy_get_results(page.get('id'), raw=True)
    backup_results = json.loads(backup_results_json)

    # if not initial_results:
    #     # if there are backup results, serve the first 4.
    #     initial_results = backup_results[:4]

    page['description'] = page.get(
        'shareText', page.get('featured-product-description', '')
    )
    page['template'] = page.get('template', 'hero') # TODO: hero? hero-image?

    attributes = {
        "campaign": page,
        "store": store,
        "columns": range(4),
        "product": json_postprocessor(product),
        "initial_results": map(json_postprocessor, initial_results),
        "backup_results": map(json_postprocessor, backup_results),
        "pub_date": datetime.now(),
        "legal_copy": page.get('legalCopy', ''),
        "mobile_hero_image": page.get('heroImageMobile', ''),
        "desktop_hero_image": page.get('heroImageDesktop', ''),
        "ir_base_url": intentrank_base_url,
        "ga_account_number": settings.GOOGLE_ANALYTICS_PROPERTY,
        }

    context = RequestContext(request, attributes)
    return context


def generate_page_theme(variables):
    # TODO: This is hella busted because theming doesn't exist yet.
    def repl(match):
        """Returns a replaced tag content for a tag, or
        the original tag if we have no data for that tag.
        """
        match_str = match.group(1)  # just the field: e.g. 'desktop_content'

        if sub_values.has_key(match_str):
            return ''.join(sub_values[match_str])
        else:
            return match.group(0)  # leave unchanged

    page_str = ''
    theme = ''
    # # theme is a temporary StoreTheme object
    # theme = campaign.theme
    # if not theme:
    #     raise ValueError('campaign has no theme when campaign manager saved it')
    #
    # # check if the theme is actually a contentgraph resource
    # try:
    #     theme_url = theme.url
    #     # 'template' is a key proposed by alex
    #     page_str = get_contentgraph_data(theme_url)['template']['results']
    # except (TypeError, ValueError):
    #     page_str = theme.page  # it's fine, this theme is a string

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
                result = result.render(variables)
            else:
                result = result.encode('unicode-escape')

            try:
                sub_values[field].append(result.decode("unicode_escape"))
            except UnicodeDecodeError:  # who knows
                sub_values[field].append(result)

    page_str = regex.sub(repl, page_str)
    return page_str


# TODO: Can this be generalized to be used anywhere?
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
                escaped_product_dict[key] = product_dict[key] \
                    .replace('\r', r'\r') \
                    .replace('\n', r'\n') \
                    .replace('"', r'\"')
            else:
                escaped_product_dict[key] = product_dict[key]

        return mark_safe(json.dumps(escaped_product_dict))
    else:
        return 'null'