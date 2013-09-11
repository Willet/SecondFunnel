from django import template
from django.template.defaultfilters import escapejs as _escapejs

register = template.Library()

@register.filter()
def escapejs(value):
    return _escapejs(value)