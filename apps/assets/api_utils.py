from django.utils import simplejson
from tastypie.serializers import Serializer


class PrettyJSONSerializer(Serializer):
    json_indent = 4

    def to_json(self, data, options = None):
        options = options or {}
        data = self.to_simple(data, options)
        return simplejson.dumps(data, sort_keys=False, indent=self.json_indent, ensure_ascii=False)
