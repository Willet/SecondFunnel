from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.api.decorators import append_headers, check_login


# login_required decorator?
from secondfunnel.errors import deprecated


@append_headers
@check_login
@never_cache
@csrf_exempt
@deprecated
def proxy_view(request, path):
    raise NotImplementedError("{0} is no longer.".format(path))
