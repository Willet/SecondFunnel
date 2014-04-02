from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from apps.api.paginator import BaseCGHandler
from apps.intentrank.utils import ajax_jsonp


class CategoryCGHandler(BaseCGHandler):
    """Categories do not exist. Emulate read-only REST API that returns nothing."""
    def get_queryset(self):
        return []

    def get(self, request, *args, **kwargs):
        return ajax_jsonp({
            'results': self.get_queryset()
        })
