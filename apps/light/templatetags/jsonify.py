import json

from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.template import Library
from django.utils.safestring import mark_safe

register = Library()


@register.filter(name='jsonify')
def jsonify(obj):
    if obj is None:
        # TODO: this should just be 'null' however
        #       our current pages info needs js's undefined right now :(
        return 'undefined'
    if isinstance(obj, QuerySet):
        json_str = mark_safe(serialize('json', obj))
    else:
        # like above... replaces all nulls with undefineds.
        # alternatively, either handle null in target source code, or do
        # costly nested replacement before dumps-ing.
        json_str = json.dumps(obj)

    return mark_safe(json_str.replace(': null', ': undefined')
                             .replace(':null', ':undefined'))
