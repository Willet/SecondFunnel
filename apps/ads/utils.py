import json

from datetime import datetime

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template import RequestContext, Template
from apps.assets.models import Theme


def render_banner(page, request):
    """Generates the HTML page for a standard pinpoint product page.

    Backup products are populated statically only if a request object
    is provided.

    :param store_id: optional, legacy, unused
    :param product: if provided, the theme may attempt to display this
                    product in the hero area
    """

    # grab required assets
    banner_theme = request.GET.get('theme', '300x600')
    page_template = get_object_or_404(Theme, name=banner_theme)

    store = page.store

    ir_base_url = '/intentrank'

    algorithm = request.GET.get('algorithm', page.feed.feed_algorithm or 'generic')

    tests = []
    if page.get('tests'):
        tests = json.dumps(page.get('tests'))

    attributes = {
        "session_id": request.session.session_key,
        "campaign": page,
        "store": store,
        "columns": range(4),
        "product": "undefined",
        "initial_results": [],  # JS now fetches its own initial results
        "backup_results": [],
        "social_buttons": '',
        "conditional_social_buttons": "{}",
        "column_width": page.column_width or 150,  # 150 = 300 / 2
        "enable_tracking": "false",  # jsbool
        "image_tile_wide": page.image_tile_wide,
        "pub_date": datetime.now().isoformat(),
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
