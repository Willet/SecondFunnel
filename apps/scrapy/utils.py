import base64
from functools import wraps
import os
import re
from scrapy.selector import SelectorList
import tempfile
import webbrowser
import cloudinary.uploader as uploader
from scrapy.http import HtmlResponse, TextResponse
from scrapy_webdriver.http import WebdriverResponse


def open_in_browser(response, _openfunc=webbrowser.open):
    """
    Open the given response in a local web browser, populating the <base>
    tag for external links to work

    Very useful for debugging a scraper.

    Duplicated from scrapy.utils.response.open_in_browser to support
    WebdriverResponse.

    For more details on usage, see:
        http://doc.scrapy.org/en/latest/topics/debug.html#open-in-browser
    """
    body = response.body
    if isinstance(response, HtmlResponse) or isinstance(response, WebdriverResponse):
        if '<base' not in body:
            body = body.replace('<head>', '<head><base href="%s">' % response.url)
        ext = '.html'
    elif isinstance(response, TextResponse):
        ext = '.txt'
    else:
        raise TypeError("Unsupported response type: %s" % \
            response.__class__.__name__)
    fd, fname = tempfile.mkstemp(ext)
    os.write(fd, body)
    os.close(fd)
    return _openfunc("file://%s" % fname)


def django_item_values(item):
    # Modified from DjangoItem.instance
    return ((k, item.get(k)) for k in item._values if k in item._model_fields)

def item_to_model(item):
    model_class = getattr(item, 'django_model')
    if not model_class:
        raise TypeError("Item is not a `DjangoItem` or is misconfigured")

    return item.instance


def get_or_create(model):
    model_class = type(model)
    created = False

    # Normally, we would use `get_or_create`. However, `get_or_create` would
    # match all properties of an object (i.e. create a new object
    # anytime it changed) rather than update an existing object.
    #
    # Instead, we do the two steps separately
    try:
        # We have no unique identifier at the moment; use the name for now.
        obj = model_class.objects.get(name=model.name)
    except model_class.DoesNotExist:
        created = True
        obj = model  # DjangoItem created a model for us.

    return (obj, created)


def update_model(destination, source_item, commit=True):
    pk = destination.pk

    for (key, value) in django_item_values(source_item):
        setattr(destination, key, value)

    setattr(destination, 'pk', pk)

    if commit:
        destination.save()

    return destination


def camel_to_underscore(name):
    """
    Converts CamelCase strings to camel_case.

    Source: http://stackoverflow.com/a/1176023

    >>> convert('CamelCase')
    'camel_case'
    >>> convert('CamelCamelCase')
    'camel_camel_case'
    >>> convert('Camel2Camel2Case')
    'camel2_camel2_case'
    >>> convert('getHTTPResponseCode')
    'get_http_response_code'
    >>> convert('get2HTTPResponseCode')
    'get2_http_response_code'
    >>> convert('HTTPResponseCode')
    'http_response_code'
    >>> convert('HTTPResponseCodeXYZ')
    'http_response_code_xyz'
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# Inspired by this: http://stackoverflow.com/a/14165844
def spider_pipelined(process_item):
    """
    A decorator for `Pipeline.process_item` to defer to spider-specific
    pipelines if they exist.

    Use this when a spider has specific steps that need to happen (instead of
    the default pipeline).

    Note: If a spider-specific pipeline exists, *this pipeline will not be
    called*

    TODO: Add flag to allow pipeline to be called.
    """

    @wraps(process_item)
    def wrapper(self, item, spider):
        class_name = self.__class__.__name__
        method_name = camel_to_underscore(class_name)

        pipeline = getattr(spider, method_name, None)
        if pipeline:
            return pipeline(item, spider)

        return process_item(item)

    return wrapper


class CloudinaryStore(object):
    def persist_file(self, path, buf, info, meta=None, headers=None):
        # This is the de facto way to upload an image (according to
        # Cloudinary support) if the image is just bytes
        b64img = base64.b64encode(buf.getvalue())
        data = 'data:{};base64,{}'.format(
            headers.get('Content-Type'),
            b64img
        )

        image = uploader.upload(
            data, folder='test', colors=True, format='jpg'
        )
        return image

    def stat_file(self, path, info):
        """
        Returns information about a file
        """
        return None


def monkeypatch_method(cls):
    """
    A decorator to replace / add a method of an existing class.

    From Guido van Rossum himself:
        https://mail.python.org/pipermail/python-dev/2008-January/076194.html
    """
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator


def django_serializer(value):
    return value.id  # serializers.serialize('json', [ value, ])


def store_serializer(value):
    django_serializer(value)