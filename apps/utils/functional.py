import os
import pkgutil
import sys
import inspect
import itertools
import urlparse

def autodiscover_module_classes(name, path, baseclass=None):
    """
    Discover every class defined in this package at the immediate depth
    Optionally filter for children of baseclass

    NOTE: usually used in an __init__.py file. Populate globals or __all__ with the output

    returns: <list> everything found
    """
    # get all immediate sub-modules
    modules = []
    for importer, package_name, _ in pkgutil.iter_modules(path, prefix="{}.".format(name)):
        if package_name not in sys.modules:
            module = importer.find_module(package_name).load_module(package_name)
        else:
            module = sys.modules[package_name]
        modules.append(module)
    # get classes in submodules
    discovered = []
    for module in modules:
        members = inspect.getmembers(module, 
                                     lambda member: inspect.isclass(member) and \
                                                    member.__module__ == module.__name__)
        for _, member in members:
            if baseclass:
                if issubclass(member, baseclass):
                    discovered.append(member)
            else:
                discovered.append(member)
    return discovered

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
