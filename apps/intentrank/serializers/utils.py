from django.core.serializers.json import Serializer as JSONSerializer
import json
import inflection

from apps.utils.classes import MemcacheSetting


class SerializerError(Exception):
    """ Exception raised for missing required parameters """
    pass


class IRSerializer(JSONSerializer):
    """This removes the square brackets introduced by the JSONSerializer."""
    MEMCACHE_PREFIX = 'ir'
    MEMCACHE_TIMEOUT = 0 # use db_cache

    @classmethod
    def dump(cls, obj, skip_cache=False):
        """obj be <Model>"""
        return cls().to_json([obj], skip_cache=skip_cache)

    def start_serialization(self):
        if json.__version__.split('.') >= ['2', '1', '3']:
            # Use JS strings to represent Python Decimal instances (ticket #16850)
            self.options.update({'use_decimal': False})
        self._current = None
        self.json_kwargs = self.options.copy()
        self.json_kwargs.pop('stream', None)
        self.json_kwargs.pop('fields', None)

    def end_serialization(self):
        """Do not want the original behaviour (adding commas)"""
        pass

    def to_json(self, queryset, **options):
        """Contrary to what the method name suggests, this

        :returns a dict.
        """
        return json.loads(self.to_str(queryset=queryset, **options))

    def to_str(self, queryset, **options):
        # single object serialization cache
        # for when an object was done more than once per request
        skip_cache = options.pop('skip_cache', False)
        if skip_cache:
            return self.serialize(queryset=queryset, **options)

        if len(queryset) == 1:
            obj = queryset[0]

            # representation already made
            if self.MEMCACHE_PREFIX == 'ir' and getattr(obj, 'ir_cache', ''):
                return getattr(obj, 'ir_cache', '')

            obj_key = "{0}-{1}-{2}".format(self.MEMCACHE_PREFIX,
                                           obj.__class__.__name__, obj.id)

            # if you have a memcache, that is
            obj_str_cache = MemcacheSetting.get(obj_key, False)
            if obj_str_cache:  # in cache, return it
                return obj_str_cache
            else:  # not in cache, save it
                obj_str = self.serialize(queryset=queryset, **options)
                MemcacheSetting.set(obj_key, obj_str,
                                    timeout=self.MEMCACHE_TIMEOUT)  # save
                return obj_str

        return self.serialize(queryset=queryset, **options)


def camelize_JSON(attributes):
    """ camelize JSON attributes """
    return { inflection.camelize(attr, False):attributes[attr] for attr in attributes }
