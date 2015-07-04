
class LookupTable(object):
    """
    A one-to-many lookup table that supports 
     - an arbitary number of lookup fields
     - arbitrary data

    Used to store datafeeds & help with matching results to DB entries

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

        mappings - a list of tuples with fields and lookup keys
        first - if True, return only the first matching entry
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
        # Didn't find anything
        return (None, None)

