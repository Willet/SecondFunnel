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

from apps.utils import noop

def render_campaign(campaign, request=None, get_seeds_func=None):
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

    # TODO: Content blocks don't make as much sense now; when to clean up?
    # TODO: If we keep content blocks, should this be a method?
    # Assume only one content block
    content_block = campaign.content_blocks.all()[0]

    product = content_block.data.product
    product.json = json.dumps(product.data(raw=True))

    campaign.stl_image = getattr(
        content_block.data, 'get_ls_image', noop)(url=True) or ''
    campaign.featured_image = getattr(
        content_block.data, 'get_image', noop)(url=True) or ''
    campaign.description = (content_block.data.description or product.description).encode('unicode_escape')
    campaign.template = slugify(
        content_block.block_type.name)

    if get_seeds_func and request:
        #

        # "borrow" IR for results
        related_results = get_seeds_func(
            request, store=campaign.store.slug,
            campaign=campaign.default_intentrank_id or campaign.id,
            base_url=settings.WEBSITE_BASE_URL + '/intentrank',
            results=100,
            raw=True
        )
    else:
        related_results = []

    if settings.DEBUG:
        base_url = settings.WEBSITE_BASE_URL
    else:
        base_url = settings.INTENTRANK_BASE_URL

    base_url += '/intentrank'

    attributes = {
        "campaign": campaign,
        "columns": range(4),
        "preview": not campaign.live,
        "product": product,
        "backup_results": json.dumps(related_results),
        "pub_date": datetime.now(),
        "base_url": base_url,
        "ga_account_number": settings.GOOGLE_ANALYTICS_PROPERTY,
    }
    if request:
        context = RequestContext(request, attributes)
    else:
        context = Context(attributes)

    theme = campaign.get_theme()

    if not theme:
        raise ValueError('Neither campaign nor its store has a theme defined')

    page_str = theme.page

    # Replace necessary tags
    sub_values = defaultdict(list)
    regex = re.compile("\{\{\s*(\w+)\s*\}\}")

    # REQUIRED is a bit of a misnomer...
    for field, details in theme.REQUIRED_FIELDS.iteritems():
        # field: e.g. 'desktop_content'
        # details: e.g. {'values': ['pinpoint/campaign_scripts_core.html',
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

            # TODO: Do we need to render, or can we just convert to string?
            # answer: we only need to convert it to a string.
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
    # TODO: Doesn't make sense but is required; why?
    rendered_page = page.render(context)
    if isinstance(rendered_page, unicode):
        rendered_page = rendered_page.encode('utf-8')

    rendered_page = unicode(rendered_page, 'utf-8')

    return rendered_page
