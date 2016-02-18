class DefaultValue(object):
    """
    Internally, ItemLoader uses a defaultdict([]). If the `arg` is `[]`, replace
    it with the desired default `value`.

    Note: if value is a [] or {}, it should be wrapped in a lambda to avoid that
    object being shared between loader instances
    """
    def __init__(self, default):
        self.value = default

    def __call__(self, arg):
        if isinstance(arg, list) and not arg:
            return self.value() if callable(self.value) else self.value
        else:
            return arg


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
