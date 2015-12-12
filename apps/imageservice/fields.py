import json

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext as _
from south.modelsinspector import add_introspection_rules

from .models import ImageSizes


class ImageSizesField(models.TextField):
    """
    Field for storing image sizes & urls. Model attribute is an <ImageSizes> instance
    
    Note: internally stored as json
    """
    __metaclass__ = models.SubfieldBase
    description = _("Indexed image size dimensions and url")
    add_introspection_rules([], ["^apps\.imageservice\.fields\.ImageSizesField"])

    def to_python(self, value):
        if not value:
            return ImageSizes()
        else:
            return ImageSizes(internal_json=value)

    def validate(self, value, model_instance):
        if not isinstance(value, ImageSizes):
            raise ValidationError(
                _(u"Must have type <ImageSizes>"),
                params={'type': type(value)},
                code='invalid',
            )
        super(ImageSizesField, self).validate(value, model_instance)

    def get_db_prep_value(self, value, connection=None, prepared=None):
        return unicode(value)

    def value_to_string(self, obj):
        # django internals
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)
