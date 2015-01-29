
class MergeDicts(object):
    """
    A processor that, given a list of values (dicts), merges the values

    Note that it does this in the stupidest way possible (i.e. later keys
    replace earlier keys) but for our purposes this is fine.
    """
    def __call__(self, values):
        itervalues = iter(values)
        result = next(itervalues, None)

        for value in itervalues:
            result.update(value)

        return result
