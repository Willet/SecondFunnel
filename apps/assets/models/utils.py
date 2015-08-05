import calendar
import datetime

from django_extensions.db.fields import CreationDateTimeField

import apps.api.serializers as cg_serializers
import apps.intentrank.serializers as ir_serializers
from apps.utils.models import MemcacheSetting


default_master_size = {
    'master': {
        'width': '100%',
        'height': '100%',
    }
}


class SerializableMixin(object):
    """Provides to_json() and to_cg_json() methods for model instances.

    To implement specific json formats, override these methods.
    """

    serializer = ir_serializers.RawSerializer
    cg_serializer = cg_serializers.RawSerializer

    def to_json(self, skip_cache=False):
        """default method for all models to have a json representation."""
        if hasattr(self.serializer, 'dump'):
            return self.serializer.dump(self, skip_cache=skip_cache)
        return self.serializer().serialize(iter([self]))

    def to_str(self, skip_cache=False):
        return self.serializer().to_str([self], skip_cache=skip_cache)

    def to_cg_json(self):
        """serialize into CG model. This is an instance shorthand."""
        return self.cg_serializer.dump(self)


class BaseModel(models.Model, SerializableMixin):
    created_at = CreationDateTimeField()
    created_at.editable = True

    # To change this value, use model.save(skip_updated_at=True)
    updated_at = models.DateTimeField(auto_now=True)

    # used by IR to bypass frequent re/deserialization to shave off CPU time
    ir_cache = models.TextField(blank=True, null=True)

    # @override
    _attribute_map = (
        # (cg attribute name, python attribute name)
        ('created', 'created_at'),
        ('last-modified', 'updated_at'),
    )

    class Meta(object):
        abstract = True

    def __getitem__(self, key):
        return getattr(self, key, None)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __unicode__(self):
        """Changes display of models in the django admin.

        http://stackoverflow.com/a/5853966/1558430
        """
        if hasattr(self, 'name'):
            return u'({class_name} #{obj_id}) {obj_name}'.format(
                class_name=self.__class__.__name__,
                obj_id=self.pk,
                obj_name=getattr(self, 'name', ''))

        return u'{class_name} #{obj_id}'.format(
            class_name=self.__class__.__name__,
            obj_id=self.pk)

    @classmethod
    def _copy(cls, obj, update_fields={}, exclude_fields=[]):
        """Copies fields over to new instance of class & saves it
        Note: Fields 'id' and 'ir_cache' are excluded by default
        Warning: not tested with all related fields

        :param obj - instance to copy
        :param update_fields - dict of key,values of fields to update
        :param exclude_fields - list of field names to exclude from copying

        :return copied instance
        """
        # NOTE: _meta API updated in Django 1.8, will need to re-implement
        default_exclude = ['id', 'ir_cache']
        autofields = [f.name for f in obj._meta.fields if isinstance(f, models.AutoField)]
        exclude = list(set(exclude_fields + autofields + default_exclude)) # eliminate duplicates

        # local fields + many-to-many fields = all fields (assumption!)
        local_fields = [f.name for f in obj._meta.local_fields]
        m2m_fields = [f.name for f in obj._meta.many_to_many]

        # Remove excluded fields from fields that are copied
        local_kwargs = { k:getattr(obj,k) for k in local_fields if k not in exclude }
        m2m_kwargs = { k:getattr(obj,k) for k in m2m_fields if k not in exclude }

        # Separate update_fields into local & m2m
        local_update = { k:v for (k,v) in update_fields.iteritems() if k in local_fields }
        m2m_update = { k:v for (k,v) in update_fields.iteritems() if k in m2m_fields }
        
        local_kwargs.update(local_update)
        m2m_kwargs.update(m2m_update)

        new_obj = cls(**local_kwargs)
        new_obj.save()

        # m2m fields require instance id, so set after saving
        for (k,v) in m2m_kwargs.iteritems():
            setattr(new_obj, k, v.all())

        new_obj.save()

        return new_obj

    def update_ir_cache(self):
        """Generates and/or updates the IR cache for the current object.
        Remember to save object to persist!

        :returns (the cache, whether it was updated)
        """
        old_ir_cache = self.ir_cache
        self.ir_cache = ''  # force tile to regenerate itself
        new_ir_cache = self.to_str(skip_cache=True)

        if new_ir_cache == old_ir_cache:
            return new_ir_cache, False

        self.ir_cache = new_ir_cache
        return new_ir_cache, True

    def _cg_attribute_name_to_python_attribute_name(self, cg_attribute_name):
        """(method name can be shorter, but something about PEP 20)

        reads the model's key conversion map and returns whichever model
        attribute name it is that matches the given cg_attribute_name.

        :returns str
        """
        for cg_py in self._attribute_map:
            if cg_py[0] == cg_attribute_name:
                return cg_py[1]
        return cg_attribute_name  # not found, assume identical

    def _python_attribute_name_to_cg_attribute_name(self, python_attribute_name):
        """(method name can be shorter, but something about PEP 20)

        reads the model's key conversion map and returns whichever model
        attribute name it is that matches the given python_attribute_name.

        :returns str
        """
        for cg_py in reversed(self._attribute_map):
            if cg_py[1] == python_attribute_name:
                return cg_py[0]
        return python_attribute_name  # not found, assume identical

    @classmethod
    def update_or_create(cls, defaults=None, **kwargs):
        """Like Model.objects.get_or_create, either gets, updates, or creates
        a model based on current state. Arguments are the same as the former.

        Examples:
        >>> Store.update_or_create(id=2, defaults={"id": 3})
        (<Store: Store object>, True, False)  # created
        >>> Store.update_or_create(id=2, defaults={"id": 3})
        (<Store: Store object>, False, False)  # found
        >>> Store.update_or_create(id=2, id=4)
        (<Store: Store object>, False, True)  # updated

        :raises <AllSortsOfException>s, depending on input
        :returns tuple  (object, updated, created)
        """
        updated = created = False

        if not defaults:
            defaults = {}

        try:
            obj = cls.objects.get(**kwargs)
            for key, value in defaults.iteritems():
                try:
                    current_value = getattr(obj, key, None)
                except ObjectDoesNotExist as err:
                    # tried to read object reference that currently
                    # points to nothing. ignore it and set the attribute.
                    # a subclass.DoesNotExist, whose reference I don't know
                    current_value = err

                if current_value != value:
                    setattr(obj, key, value)
                    updated = True

        except cls.DoesNotExist:
            update_kwargs = dict(defaults.items())
            update_kwargs.update(kwargs)
            obj = cls(**update_kwargs)
            created = True

        if created or updated:
            obj.save()

        return (obj, created, updated)

    def get(self, key, default=None):
        """Duck-type a <dict>'s get() method to make CG transition easier.

        Also looks into the attributes JSONField if present.
        """
        attr = getattr(self, key, None)
        if attr:
            return attr
        if hasattr(self, 'attributes'):
            if key in self.attributes:
                return self.attributes.get(key, default)
        return default

    def update(self, other=None, **kwargs):
        """This is not <dict>.update().

        Setting attributes of non-model fields does not raise exceptions..

        :param {dict} other    overwrites matching attributes in self.
        :param {dict} kwargs   only if other is not supplied, use kwargs
                               as other.

        :returns self (<dict>.update() does not return anything)
        """
        if not other:
            other = kwargs

        if not other:
            return self

        for key in other:
            if key == 'created':
                self.created_at = datetime.datetime.fromtimestamp(
                    int(other[key]) / 1000)
            elif key in ['last-modified', 'modified']:
                self.updated_at = datetime.datetime.fromtimestamp(
                    int(other[key]) / 1000)
            else:
                setattr(self,
                        self._cg_attribute_name_to_python_attribute_name(key),
                        other[key])
            print u"updated {0}.{1} to {2}".format(
                self, self._cg_attribute_name_to_python_attribute_name(key),
                other[key])

        return self

    def save(self, *args, **kwargs):
        self.full_clean()

        if hasattr(self, 'pk') and self.pk:
            obj_key = "cg-{0}-{1}".format(self.__class__.__name__, self.id)
            MemcacheSetting.set(obj_key, None)  # save

        super(BaseModel, self).save(*args, **kwargs)

    @property
    def cg_created_at(self):
        """(readonly) representation of the content graph timestamp"""
        return unicode(calendar.timegm(self.created_at.utctimetuple()) * 1000)

    @property
    def cg_updated_at(self):
        """(readonly) representation of the content graph timestamp"""
        return unicode(calendar.timegm(self.updated_at.utctimetuple()) * 1000)

