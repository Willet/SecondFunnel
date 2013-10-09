"""
Various utilities to assist and share among components of the PinPoint app
"""
import json
import re
from collections import defaultdict
from datetime import datetime

from django.conf import settings
from django.template import Context, RequestContext, Template, loader
from django.template.defaultfilters import slugify, safe

from apps.pinpoint.models import StoreTheme
from apps.static_pages.utils import get_remote_data
from apps.utils import noop

def render_campaign(campaign, request, get_seeds_func=None):
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

    def create_theme_from_data(theme_data):
        return StoreTheme(json.loads(theme_data))

    # TODO: Content blocks don't make as much sense now; when to clean up?
    # TODO: If we keep content blocks, should this be a method?
    # Assume only one content block
    content_block = campaign.content_blocks.all()[0]

    product = content_block.data.product

    campaign.description = (content_block.data.description or product.description).encode('unicode_escape')
    campaign.template = slugify(
        content_block.block_type.name)

    # Dirty hack
    if settings.DEBUG or re.search(r'native shoes', campaign.store.name, re.I):
        # If in debug mode, or we otherwise need to use the old proxy
        base_url = settings.WEBSITE_BASE_URL + '/intentrank'
    else:
        base_url = settings.INTENTRANK_BASE_URL + '/intentrank'

    # "borrow" IR for results
    if get_seeds_func:
        backup_results = get_seeds_func(request, store=campaign.store.slug,
            campaign=campaign.default_intentrank_id or campaign.id,
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
        theme_data = campaign.theme  # likely transition

        if not theme_data:
            raise ValueError('campaign has no theme when campaign manager saved it')

        # page_str = theme.page
        theme = create_theme_from_data(theme_data)  # likely transition
    except ValueError:
        raise  # TODO: otherwise...?

    page_str = theme.page

    # Replace necessary tags
    sub_values = defaultdict(list)
    regex = re.compile("\{\{\s*(\w+)\s*\}\}")

    # REQUIRED is a bit of a misnomer...
    for field, details in theme.REQUIRED_FIELDS.iteritems():
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
