import json
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template import RequestContext, loader
from django.views.decorators.cache import cache_page, cache_control

from apps.assets.models import Page
from apps.intentrank.controllers import IntentRank
from apps.light.utils import get_algorithm

@cache_control(must_revalidate=True, max_age=(1 * 60))
@cache_page(60 * 1, key_prefix="ad-")
def ad_banner(request, page_id):
    """Generates the page for a standard pinpoint banner ad."""
    page = get_object_or_404(Page, id=page_id)

    # grab required assets
    store = page.store

    ir_base_url = '/intentrank'

    algorithm = get_algorithm(request=request, page=page)

    tests = []
    if page.get('tests'):
        tests = json.dumps(page.get('tests'))

    ir = IntentRank(page=page)
    initial_results = ir.get_results(request=request, content_only=True, results=20)

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
        "enable_tracking": "true" if (page.id == 20) else "false",  # jsbool, TODO: remove hack for page 20
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
    template = loader.select_template(["light/%s" % page.theme.template])

    # Render response
    return HttpResponse(template.render(context))
