from django import template

register = template.Library()


@register.filter
def get_range(value):
    """
    Template tag filter.  Essentially returns a range object
    for iteration.
    """
    return range(value)


