import collections
from django.db import models
from django.test import TestCase
import json
import mock

from apps.assets.models import Tile
from apps.intentrank.serializers.utils import IRSerializer, camelize_JSON


class MockSerializer(IRSerializer):
    def serialize(self, queryset, **options):
        # Mock the internals of django.core.serializers.json
        return json.dumps(dict(queryset[0]))


class MockDjangoObj(collections.Mapping):
    serializer = MockSerializer
    ir_cache = '{"cache": "test"}'

    def __init__(self, uid, internal):
        self.id = uid
        self.internal = internal

    def __iter__(self):
        return iter(self.internal)

    def __len__(self):
        return len(self.internal)

    def __getitem__(self, key):
        return self.internal[key]


class CamelizeJSONTest(TestCase):
    def test(self):
        camelized_json = camelize_JSON({'a': 1, 'a_b': 2, 'a_b_c': 3})
        self.assertEqual(camelized_json, {'a':1, 'aB': 2, 'aBC': 3})


class IRSerializerTest(TestCase):
    s = MockSerializer()
    obj1 = MockDjangoObj(0, {'a': 1, 'b': 'cdef',})
    obj2 = MockDjangoObj(1, {'a': 3, 'b': 'o',})

    def to_str_test(self):
        self.assertEqual(self.s.to_str([self.obj1], skip_cache=True), json.dumps(dict(self.obj1)))

    def to_str_ir_cache_test(self):
        self.assertEqual(self.s.to_str([self.obj1], skip_cache=False), self.obj1.ir_cache)

    def to_str_no_obj_test(self):
        self.assertEqual(self.s.to_str([]), '')
        self.assertEqual(self.s.to_str(Tile.objects.none()), '')

    def to_str_multiple_obj_test(self):
        # With multiple objects, it should use django.core.serializers.json.Serializer
        with mock.patch('apps.intentrank.serializers.utils.JSONSerializer.serialize',
                        mock.Mock(return_value='')) as mock_serializer:
            self.s.to_str([self.obj1, self.obj2])
            mock_serializer.assert_called_with(queryset=[self.obj1, self.obj2])

    def to_json_test(self):
        self.assertEqual(self.s.to_json([self.obj1], skip_cache=True), [dict(self.obj1)])

    def to_json_test(self):
        self.assertEqual(self.s.to_json([self.obj1], skip_cache=False), json.loads(self.obj1.ir_cache))

    def to_json_no_obj_test(self):
        with self.assertRaises(ValueError):
            self.s.to_json([])

        with self.assertRaises(ValueError):
            self.s.to_json(Tile.objects.none())

    def to_json_multiple_obj_test(self):
        return_value = json.dumps([dict(self.obj1), dict(self.obj2)])
        with mock.patch('apps.intentrank.serializers.utils.JSONSerializer.serialize',
                        mock.Mock(return_value=return_value)) as mock_serializer:
            self.assertEqual(self.s.to_json([self.obj1, self.obj2]), [dict(self.obj1), dict(self.obj2)])
            mock_serializer.assert_called_with(queryset=[self.obj1, self.obj2])

    def dump_test(self):
        self.assertEqual(self.s.dump(self.obj1, skip_cache=True), dict(self.obj1))
