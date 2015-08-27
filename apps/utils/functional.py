import os
import itertools
import urlparse

def flatten(list_of_lists):
    """ Compress of a lists of lists down to just the values of the lists """
    return list(itertools.chain(*list_of_lists))

def check_keys_exist(dct, keys):
    """Returns true if all keys exist in the dict dct."""
    return all(item in dct for item in keys)

def check_other_keys_dont_exist(dct, keys):
    """Returns true if no other keys exist in the dictionary, other than
    the ones specified by the keys variable.

    this function returns true if the dict is missing those keys (because
    it is still true that other keys don't exist).
    """
    dct_key_set = set(dct.keys())
    key_set = set(keys)
    return len(list(dct_key_set - key_set)) == 0

def find_where(lst, obj_id):
    for item in lst:
        if item.id == obj_id:
            return item
    raise ValueError("object {id} not in list".format(id=obj_id))

def get_image_file_type(image_url):
    """Returns the file type of the image from given url string, image_url.
    """
    return os.path.splitext(urlparse.urlparse(image_url).path)[1][1:]

def may_be_json(obj, attr, expected_cls):
    """
    Try to load JSON, catch ValueError if its not well formatted JSON

    @param obj - obj containing attr with potential JSON
    @param attr - name of attribute to look up on obj
    @param expected_cls - resulting class, will return empty instance of this
    """
    maybe = getattr(obj, attr, expected_cls())
    if isinstance(obj, basestring):
        try:
            maybe = json.loads(maybe)
        except ValueError:
            # wasn't JSON
            pass
    if not isinstance(maybe, expected_cls):
        maybe = expected_cls()
    return maybe
