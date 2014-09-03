import json
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template import RequestContext, loader
from django.views.decorators.cache import cache_page, cache_control

from apps.assets.models import Page
from apps.intentrank.controllers import IntentRank
from apps.intentrank.serializers import PageConfigSerializer
from apps.light.utils import get_algorithm

@cache_control(must_revalidate=True, max_age=(1 * 60))
@cache_page(60 * 1, key_prefix="ad-")
def ad_banner(request, page_id):
    """Generates the page for a standard pinpoint banner ad."""
    page = get_object_or_404(Page, id=page_id)

    # grab required assets
    store = page.store
    tile = None  # this is fine

    tests = []
    if page.get('tests'):
        tests = json.dumps(page.get('tests'))

    ir_base_url = '/intentrank'

    algorithm = get_algorithm(request=request, page=page)
    PAGES_INFO = PageConfigSerializer.to_json(request=request, page=page,
        feed=page.feed, store=store, algorithm=algorithm, featured_tile=tile,
        other={'tile_set': 'content'})

    ir = IntentRank(page=page)
    initial_results = ir.get_results(request=request, content_only=True, results=20)

    initial_results = [x.to_json() for x in initial_results]

    attributes = {
        "algorithm": algorithm,
        "campaign": page,
        "columns": range(4),
        "column_width": page.column_width or 150,  # 150 = 300 / 2
        "conditional_social_buttons": "{}",
        "enable_tracking": "true" if (page.id == 20) else "false",  # jsbool, TODO: remove hack for page 20
        "environment": settings.ENVIRONMENT,
        "ga_account_number": settings.GOOGLE_ANALYTICS_PROPERTY,
        "image_tile_wide": page.image_tile_wide,
        "initial_results": json.dumps(initial_results),
        "ir_base_url": ir_base_url,
        "keen_io": settings.KEEN_CONFIG,
        "open_tile_in_popup": "true",
        "PAGES_INFO": PAGES_INFO,
        "product": "undefined",
        "pub_date": datetime.now().isoformat(),
        "session_id": request.session.session_key,
        "social_buttons": '',
        "store": store,
        "tests": tests,
        "tile": tile,
        "url": page.get('url', ''),
        "url_params": json.dumps(page.get("url_params", {})),
    }

    context = RequestContext(request, attributes)

    # Page content
    template = loader.select_template(["light/%s" % page.theme.template])

    # Render response
    return HttpResponse(template.render(context))
