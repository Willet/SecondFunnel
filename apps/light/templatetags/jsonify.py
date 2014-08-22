import json

from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.template import Library
from django.utils.safestring import mark_safe

register = Library()


@register.filter(name='jsonify')
def jsonify(obj):
    if obj == None:
        # TODO: this should just be 'null' however
        #       our current pages info needs js's undefined right now :(
        return 'undefined'
    if isinstance(obj, QuerySet):
        return mark_safe(serialize('json', obj))
    return mark_safe(json.dumps(obj))
