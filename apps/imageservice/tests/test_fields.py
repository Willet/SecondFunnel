from django.core.exceptions import ValidationError
from django.test import TestCase
import mock

from apps.imageservice.fields import ImageSizesField
from apps.imageservice.models import ImageSizes


class ImageSizesFieldTest(TestCase):
    name = 'w400'
    size = {'width': 400, 'url': 'http://images.secondfunnel.com/foo/bar.jpg'}

    def setUp(self):
        self.empty_value = ImageSizes()
        self.full_value = ImageSizes()
        self.full_value[self.name] = self.size
        self.json_value = unicode(self.full_value)
        self.field = ImageSizesField("test")

    def to_python_no_value_test(self):
        r = self.field.to_python('')
        self.assertEqual(r, self.empty_value)

    def to_python_value_test(self):
        r = self.field.to_python(unicode(self.full_value))
        self.assertEqual(r, self.full_value)

    def validate_test(self):
        # No ValidationError
        self.field.validate(self.empty_value, mock.Mock())

    def validate_fail_test(self):
        with self.assertRaises(ValidationError):
            self.field.validate('', mock.Mock())

    def get_db_prep_value_test(self):
        r = self.field.get_db_prep_value(self.full_value)
        self.assertEqual(r, self.json_value)

    def get_db_prep_value_empty_test(self):
        r = self.field.get_db_prep_value(self.empty_value)
        self.assertEqual(r, u'{}')
