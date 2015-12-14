import json
from mock import patch, call
from unittest import TestCase

from apps.imageservice.models import ImageSizes
from apps.imageservice.utils import delete_resource


class ImageSizesTest(TestCase):
    name = 'w400'
    name2 = 'h500'
    size = {'width': 400, 'url': 'http://images.secondfunnel.com/foo/bar.jpg'}
    size2 = {'width': 400, 'height': 400, 'url': 'http://images.secondfunnel.com/foo/bar.jpg'}
    size3 = {'width': 400, 'url': 'http://images.secondfunnel.com/zaz/zle.jpg'}
    size4 = {'width': 500, 'url': 'http://images.secondfunnel.com/bea/tle.jpg'}
    size5 = {'height': 500, 'url': 'http://images.secondfunnel.com/bea/tle.jpg'}

    def setUp(self):
        self.img_sizes = ImageSizes()

    def init_test(self):
        self.assertTrue(len(self.img_sizes) == 0)

    def init_internal_json_test(self):
        self.img_sizes[self.name] = self.size
        internal_json = unicode(self.img_sizes)
        img_sizes = ImageSizes(internal_json=internal_json)
        self.assertEqual(img_sizes, self.img_sizes)

    def add_test(self):
        # add new size, should not call _remove
        with patch.object(self.img_sizes, '_remove'):
            self.img_sizes[self.name] = self.size

            self.img_sizes._remove.assert_not_called()
            self.assertTrue(len(self.img_sizes) == 1)
            self.assertEqual(self.img_sizes[self.name], self.size)

    def add_overwrite_test(self):
        # overwrite with same name & same url, should not call _remove
        self.img_sizes[self.name] = self.size

        with patch.object(self.img_sizes, '_remove'):
            self.img_sizes[self.name] = self.size2

            self.img_sizes._remove.assert_not_called()
            self.assertTrue(len(self.img_sizes) == 1)
            self.assertEqual(self.img_sizes[self.name], self.size2)

    def add_overwrite_with_url_test(self):
        # overwrite with same name & different urls, should call _remove
        self.img_sizes[self.name] = self.size

        with patch.object(self.img_sizes, '_remove'):
            self.img_sizes[self.name] = self.size3

            self.img_sizes._remove.assert_called_once_with(self.name, delete_resource=True)
            self.assertTrue(len(self.img_sizes) == 1)
            self.assertEqual(self.img_sizes[self.name], self.size3)

    def contains_test(self):
        self.img_sizes[self.name] = self.size

        self.assertTrue(self.name in self.img_sizes)

    def unicode_test(self):
        # unicode should just be a json dump of the internal dict
        self.img_sizes[self.name] = self.size

        self.assertEqual(unicode(self.img_sizes), json.dumps({self.name: self.size}))

    def equality_test(self):
        self.img_sizes[self.name] = self.size
        other = ImageSizes()
        other[self.name] = self.size

        self.assertEqual(self.img_sizes, other) # identical
        self.assertNotEqual(self.img_sizes, '') # different types
        self.assertNotEqual(self.img_sizes, ImageSizes()) # full vs empty ImageSizes

    def find_size_width_test(self):
        self.img_sizes[self.name] = self.size # size with only width 400

        # Match
        self.assertEqual((self.name, self.size), self.img_sizes.find({'width': 400}))
        # No match
        self.assertEqual((None, None), self.img_sizes.find({'width': 500}))

    def find_size_height_test(self):
        self.img_sizes[self.name] = self.size5 # size with only height 500

        # Match
        self.assertEqual((self.name, self.size5), self.img_sizes.find({'height': 500}))
        # No match
        self.assertEqual((None, None), self.img_sizes.find({'height': 600}))

    def find_name_test(self):
        with self.assertRaises(ValueError):
            self.img_sizes.find(u'blah')

    @patch('apps.imageservice.models.delete_remote_resource')
    def delete_test(self, mock_delete_resource):
        self.img_sizes[self.name] = self.size
        del self.img_sizes[self.name]

        self.assertEqual(len(self.img_sizes), 0)

    @patch('apps.imageservice.models.delete_remote_resource')
    def remove_name_test(self, mock_delete_resource):
        self.img_sizes[self.name] = self.size
        self.img_sizes._remove(self.name, delete_resource=False)

        self.assertFalse(self.name in self.img_sizes)
        mock_delete_resource.assert_not_called()

    @patch('apps.imageservice.models.delete_remote_resource')
    def remove_name_and_delete_resource_test(self, mock_delete_resource):
        self.img_sizes[self.name] = self.size
        self.img_sizes._remove(self.name, delete_resource=True)

        mock_delete_resource.assert_called_once_with(self.size['url'])

    def delete_resources_test(self):
        with patch.object(self.img_sizes, '_remove'):
            self.img_sizes.delete_resources() # No resources
            
            self.assertEqual(self.img_sizes._remove.call_count, 0)

            self.img_sizes[self.name] = self.size
            self.img_sizes[self.name2] = self.size5
            self.img_sizes.delete_resources() # 2 resources

            calls = [call(self.name, delete_resource=True), call(self.name2, delete_resource=True)]
            self.img_sizes._remove.assert_has_calls(calls, any_order=True)
            self.assertEqual(self.img_sizes._remove.call_count, 2)
