"""
Various utilities to assist and share among components of the PinPoint app
"""
import json
import re
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
    campaign.description = safe(
        content_block.data.description or product.description)
    campaign.template = slugify(
        content_block.block_type.name)

    if get_seeds_func and request:
        # "borrow" IR for results
        related_results = get_seeds_func(request, store=campaign.store.slug,
                                    campaign=campaign.id,
                                    seeds=product.id,
                                    results=100,
                                    raw=True)
    else:
        related_results = []

    attributes = {
        "campaign": campaign,
        "columns": range(4),
        "preview": not campaign.live,
        "product": product,
        "backup_results": json.dumps(related_results),
        "pub_date": datetime.now(),
        "base_url": settings.WEBSITE_BASE_URL
    }
    if request:
        context = RequestContext(request, attributes)
    else:
        context = Context(attributes)

    theme = campaign.get_theme(request.flavour)

    if not theme:
        #TODO: ERROR
        pass

    page_str = theme.page

    # Replace necessary tags
    for field, details in theme.REQUIRED_FIELDS.iteritems():
        field_type = details.get('type')
        values = details.get('values')

        sub_values = []
        for value in values:

            if field_type == "template":
                result = loader.get_template(value)

            elif field_type == "theme":
                result = getattr(theme, value)

            else:
                result = None

            # TODO: Do we need to render, or can we just convert to string?
            if isinstance(result, Template):
                result = result.render(context)

            else:
                result = result.encode('unicode-escape')

            sub_values.append(result)

        regex = r'\{\{\s*' + field + '\s*\}\}'
        page_str = re.sub(regex, ''.join(sub_values), page_str)

    # Page content
    page = Template(page_str)

    # Render response
    # TODO: Doesn't make sense but is required; why?
    rendered_page = page.render(context)
    if isinstance(rendered_page, unicode):
        rendered_page = rendered_page.encode('utf-8')

    rendered_page = unicode(rendered_page, 'utf-8')

    return rendered_page
