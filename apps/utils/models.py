from django.core.cache import cache


class AttrDict(dict):
    """
    A wrapper on a dict that allows dict keys to be accessed like obj attributes
    """
    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value


class LookupTable(object):
    """
    A one-to-many lookup table that supports 
     - arbitary number of lookup fields
     - arbitrary data

    Useful, for example, to store datafeeds & help with matching results to DB entries

    Note: the lookup table does not gaurentee the uniqueness of entries
    """
    def __init__(self, lookup_fields):
        self._field_lookups = {}
        self._hash_table = {}

        for f in lookup_fields:
            self._field_lookups[f] = {}

    def add(self, entry, mappings):
        """
        adds entry with the lookups in mappings

        entry - arbitrary data
        mappings - a list of tuples with field:key lookups

        raises: KeyError if lookup field was not initialized
        """
        h = id(entry)

        self._hash_table[h] = entry
        for (field, key) in mappings:
            try:
                self._field_lookups[field]
            except KeyError:
                raise KeyError('Lookup field does not exist')

            try:
                hashes = self._field_lookups[field][key]
            except KeyError:
                hashes = []
            hashes.append(h)
            self._field_lookups[field][key] = hashes

    def find(self, mappings, first=False):
        """
        searches for matching entry in order of mappings list
        stops search with first successful field:key mapping and will return
        all entries for that field:key

        @param mappings - a list of tuples with fields and lookup keys
        @param first - if True, return only the first matching entry

        @returns <tuple> found: (entries found, field found in) or not found: (None, None)
        """
        entries = []
        for (field, key) in mappings:
            try:
                self._field_lookups[field]
            except KeyError:
                raise KeyError('Lookup field does not exist')
            try:
                hashes = self._field_lookups[field][key]
            except KeyError:
                pass
            else:
                for h in hashes:
                    entries.append(self._hash_table[h])
                if first:
                    return (entries[0], field)
                else:
                    return (entries, field)
        return (None, None)


class MemcacheSetting(object):
    """Memcache setting wrapper that does not access the DB, which expires
    every half hour.

    If you don't have memcache, nothing happens.
    """

    #@classattribute
    settings = []

    setting_name = None

    @classmethod
    def get(cls, setting_name, default):
        """
        Defaults are REQUIRED; None means cache miss.
        """
        result = cache.get(setting_name, default=default)
        cls._add_key(setting_name)
        return result

    @classmethod
    def set(cls, setting_name, setting_value=None, timeout=1800):
        """None is Django's signal for a cache miss. DO NOT STORE NONES."""
        if setting_value == None:
            cache.delete(setting_name)
        else:
            cls._add_key(setting_name)
            cache.set(setting_name, setting_value, timeout=timeout)

        return cls

    @classmethod
    def keys(cls):
        """Retrieves a list of keys memcached manually."""
        if not cls.settings:
            keys_ = cls.get('memcached_keys', '').split(',')
            cls.settings = keys_

        return cls.settings

    @classmethod
    def _add_key(cls, key):
        cls.settings.append(key)
        cls.settings = list(set(cls.settings))
        cache.set('memcached_keys', ','.join(cls.settings), timeout=10000)
