from django.db.models.base import ModelBase
import mock
from unittest import TestCase

from apps.assets.models import BaseModel, Store, Theme

"""

We are avoiding fixtures because they are so slow:
http://www.mattjmorrison.com/2011/09/mocking-django.html

"""

class BaseModelTest(TestCase):
    def setUp(self):
        # create a dummy model to inherit abstract class BaseModel
        self.model = ModelBase(BaseModel)

class StoreTest(TestCase):
    # Store has no methods
    pass

class ThemeTest(TestCase):
    # Theme has no methods
    pass
