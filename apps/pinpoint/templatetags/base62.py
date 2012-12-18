from django import template

import apps.pinpoint.base62 as base62

register = template.Library()


@register.filter
def encode(value):
    return base62.encode(value)


@register.filter
def decode(value):
    return base62.decode(value)
