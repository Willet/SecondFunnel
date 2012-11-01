from django import template
from django.conf import settings
from django.db.models import Q
from django.template.loader import render_to_string
from django.template import Context

from apps.pinpoint.models import BlockContent

register = template.Library()


@register.inclusion_tag('analyticsui/analytics_data.html')
def ui_analytics_data(store=None, campaign=None):
    return {'store': store, 'campaign': campaign}
