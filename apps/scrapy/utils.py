import base64
from functools import wraps
import os
import re
from scrapy.selector import SelectorList
import tempfile
import webbrowser
import cloudinary.uploader as uploader
from django.forms import model_to_dict
from scrapy.http import HtmlResponse, TextResponse
from scrapy_webdriver.http import WebdriverResponse


def open_in_browser(response, _openfunc=webbrowser.open):
    """Open the given response in a local web browser, populating the <base>
    tag for external links to work
    """
    # XXX: this implementation is a bit dirty and could be improved
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


def update_model(destination, source, commit=True):
    pk = destination.pk

    source_dict = model_to_dict(source)
    for (key, value) in source_dict.items():
        setattr(destination, key, value)

    setattr(destination, 'pk', pk)

    if commit:
        destination.save()

    return destination


def camel_to_underscore(name):
    """
    Converts CamelCase strings to camel_case

    http://stackoverflow.com/a/1176023
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# Inspired by this: http://stackoverflow.com/a/14165844
def spider_pipelined(process_item):
    """
    A decorator for `Pipeline.process_item` to defer to spider-specific
    pipelines if they exist.

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
    def _upload(self):
        pass

    def persist_file(self, path, buf, info, meta=None, headers=None):
        """
        Uploads the file to Cloudinary
        """
        # Fuck it; for whatever reason, can't save cStringIO
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
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator


# TODO: Where does this belong
# MonkeyPatch SelectorList to add useful methods
@monkeypatch_method(SelectorList)
def extract_first(self):
    items = iter(self.extract())
    return next(items, None)