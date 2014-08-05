import json

from datetime import datetime

from django.conf import settings
from django.template import RequestContext, Template
from apps.intentrank.controllers import IntentRank
from apps.pinpoint.utils import get_algorithm


def render_banner(page, request):
    """Generates the HTML page for a standard pinpoint banner ad."""

    # grab required assets
    page_template = page.theme.load_theme()
    store = page.store

    ir_base_url = '/intentrank'

    algorithm = get_algorithm(request=request, page=page)

    tests = []
    if page.get('tests'):
        tests = json.dumps(page.get('tests'))

    ir = IntentRank(page=page)
    initial_results = ir.get_results(content_only=True, results=20,
                                     request=request)

    initial_results = [x.to_json() for x in initial_results]

    attributes = {
        "session_id": request.session.session_key,
        "campaign": page,
        "store": store,
        "columns": range(4),
        "product": "undefined",
        "open_tile_in_popup": "true",
        "initial_results": json.dumps(initial_results),
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
        "tile_set": "content",
        "url": page.get('url', ''),
        "url_params": json.dumps(page.get("url_params", {})),
        "algorithm": algorithm,
        "environment": settings.ENVIRONMENT,
        "tests": tests,
    }

    context = RequestContext(request, attributes)

    # Page content
    page = Template(page_template)

    # Render response
    return page.render(context)
