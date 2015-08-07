from django.core.exceptions import ValidationError
from django.db import models
import ast

class ListField(models.TextField):
    """
    type: (optional) type of list elements. Raises ValidationError during save if other types are added

    If we ever update to Django 1.8, this can be replaced with django.contrib.postgres.fields.ArrayField
    """
    __metaclass__ = models.SubfieldBase
    description = "Stores a python list consisting of built-in types"

    def __init__(self, *args, **kwargs):
        self.type = kwargs.pop('type') if kwargs.get('type') else None

        super(ListField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            value = []

        if isinstance(value, list):
            return value

        return ast.literal_eval(value)

    def validate(self, value, model_instance):
        if not isinstance(value, list):
            raise ValidationError("List has been over-written into '{}'".format(value))
        if self.type:
            for val in value:
                if not isinstance(val, self.type):
                    raise ValidationError("'{}' is not of {}.".format(val, self.type))

        super(ListField, self).validate(value, model_instance)

    def get_db_prep_value(self, value, connection=None, prepared=None):
        return unicode(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)