import inflection

from apps.api.serializers import RawSerializer


class SerializerError(Exception):
    """ Exception raised for missing required parameters """
    pass


class IRSerializer(RawSerializer):
    MEMCACHE_PREFIX = 'ir'
    MEMCACHE_TIMEOUT = 0  # use db cache

def camelize_JSON(attributes):
    """ camelize JSON attributes """
    return { inflection.camelize(attr, False):attributes[attr] for attr in attributes }
