import json
from mock import patch
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
        self.assertDictEqual(self.img_sizes._sizes, {})

    def init_internal_json_test(self):
        self.img_sizes.add(self.name, self.size)
        internal_json = unicode(self.img_sizes)
        img_sizes = ImageSizes(internal_json=internal_json)
        self.assertEqual(img_sizes, self.img_sizes)

    def add_test(self):
        # add new size, should not call remove
        with patch.object(self.img_sizes, 'remove'):
            self.img_sizes.add(self.name, self.size)

            self.img_sizes.remove.assert_not_called()
            self.assertTrue(len(self.img_sizes._sizes) == 1)
            self.assertEqual(self.img_sizes._sizes[self.name], self.size)

    def add_overwrite_test(self):
        # overwrite with same name & same url, should not call remove
        self.img_sizes.add(self.name, self.size)

        with patch.object(self.img_sizes, 'remove'):
            self.img_sizes.add(self.name, self.size2)

            self.img_sizes.remove.assert_not_called()
            self.assertTrue(len(self.img_sizes._sizes) == 1)
            self.assertEqual(self.img_sizes._sizes[self.name], self.size2)

    def add_overwrite_with_url_test(self):
        # overwrite with same name & different urls, should call remove
        self.img_sizes.add(self.name, self.size)

        with patch.object(self.img_sizes, 'remove'):
            self.img_sizes.add(self.name, self.size3)

            self.img_sizes.remove.assert_called_once_with(self.name, delete_resource=True)
            self.assertTrue(len(self.img_sizes._sizes) == 1)
            self.assertEqual(self.img_sizes._sizes[self.name], self.size3)

    def unicode_test(self):
        # unicode should just be a json dump of the internal dict
        self.img_sizes.add(self.name, self.size)

        self.assertEqual(unicode(self.img_sizes), json.dumps({self.name: self.size}))

    def equality_test(self):
        self.img_sizes.add(self.name, self.size)
        other = ImageSizes()
        other.add(self.name, self.size)

        self.assertEqual(self.img_sizes, other) # identical
        self.assertNotEqual(self.img_sizes, '') # different types
        self.assertNotEqual(self.img_sizes, ImageSizes()) # full vs empty ImageSizes

    def find_name_test(self):
        self.img_sizes.add(self.name, self.size)

        # Match
        self.assertEqual((self.name, self.size), self.img_sizes.find(self.name))
        # No match
        self.assertEqual(None, None), self.img_sizes.find(u'blah')

    def find_size_width_test(self):
        self.img_sizes.add(self.name, self.size) # size with only width 400

        # Match
        self.assertEqual((self.name, self.size), self.img_sizes.find({'width': 400}))
        # No match
        self.assertEqual((None, None), self.img_sizes.find({'width': 500}))

    def find_size_height_test(self):
        self.img_sizes.add(self.name, self.size5) # size with only height 500

        # Match
        self.assertEqual((self.name, self.size5), self.img_sizes.find({'height': 500}))
        # No match
        self.assertEqual((None, None), self.img_sizes.find({'height': 600}))

    @patch('apps.imageservice.models.delete_remote_resource')
    def remove_name_test(self, mock_delete_resource):
        self.img_sizes.add(self.name, self.size)
        self.img_sizes.remove(self.name, delete_resource=False)

        self.assertFalse(self.name in self.img_sizes._sizes)
        mock_delete_resource.assert_not_called()

    @patch('apps.imageservice.models.delete_remote_resource')
    def remove_name_and_delete_resource_test(self, mock_delete_resource):
        self.img_sizes.add(self.name, self.size)
        self.img_sizes.remove(self.name, delete_resource=True)

        mock_delete_resource.assert_called_once_with(self.size['url'])
