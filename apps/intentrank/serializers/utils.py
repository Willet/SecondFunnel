from apps.api.serializers import RawSerializer


class SerializerError(Exception):
    """ Exception raised for missing required parameters """
    pass


class IRSerializer(RawSerializer):
    MEMCACHE_PREFIX = 'ir'
    MEMCACHE_TIMEOUT = 0  # use db cache