from django import template

import apps.utils.base62 as base62

register = template.Library()


@register.filter
def base62_encode(value):
    return base62.encode(value)
