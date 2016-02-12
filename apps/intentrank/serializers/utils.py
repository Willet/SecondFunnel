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
        """ Shortcut for dumping json dict repr of a single object """
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
        """ get json dict repr of obj(s)

        queryset - either <QuerySet> or <list> of <Model>'s

        :returns <dict> json-esque key:value repr of obj
        """
        return json.loads(self.to_str(queryset=queryset, **options))

    def to_str(self, queryset, **options):
        """ get string of json respresentation of object

        For single objects, checks pre-generated ir_cache, then memcache, finally serializes
        For multiple objects, serializes immediately into a list

        queryset - either <QuerySet> or <list> of <Model>'s
        options - 'skip_cache' - serialize single obj
                ...other options passed through to serialize

        :return <str> json-encoded dump of obj(s)
        """
        if len(queryset) == 0:
            obj_str = ''
        elif len(queryset) > 1:
            # Serializing multiple objects, need containing brackets
            obj_str = super(IRSerializer, self).serialize(queryset=queryset, **options)
        elif options.pop('skip_cache', False):
            # Force skip caching layers
            obj_str = self.serialize(queryset=queryset, **options)
        else:
            # lookup single object in cache
            obj = queryset[0]

            # get pre-generated cache
            obj_str = getattr(obj, 'ir_cache', '')

            if not obj_str:
                # lookup memcache, only cached if same obj is serialized
                # multiple times in same operation.
                obj_key = "{0}-{1}-{2}".format(self.MEMCACHE_PREFIX,
                                               obj.__class__.__name__, obj.id)
                obj_str = MemcacheSetting.get(obj_key, False)

                if not obj_str:
                    # not in cache, generate & save it
                    obj_str = self.serialize(queryset=queryset, **options)
                    MemcacheSetting.set(obj_key, obj_str,
                                        timeout=self.MEMCACHE_TIMEOUT) # save
        return obj_str


def camelize_JSON(attributes):
    """ camelize JSON attributes """
    return { inflection.camelize(key, False):val for key, val in attributes.items() }
