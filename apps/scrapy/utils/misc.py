import base64
import bleach
from cloudinary import uploader as uploader
import decimal
import logging
import os
import re
import six
from StringIO import StringIO
import tempfile
import webbrowser

from scrapy.http import HtmlResponse, TextResponse
from scrapy_webdriver.http import WebdriverResponse


class CarefulStringIO(StringIO, object):
    """ StringIO.StringIO errors when streamed a mixture of unicode and str. Force
    unicode conversion

    NOTE magic: requires `object` as mixin b/c StringIO is old-style class that `super`
    doesn't recognize. """
    def write(self, string, *args, **kwargs):
        super(CarefulStringIO, self).write(unicode(string), *args, **kwargs)


class ExceptionStatsLogger(logging.Handler):
    """ Log exceptions to the Scrapy stats collection 

    Scrapy exceptions beyond outside of the crawler are not conviently
    collected. """
    def __init__(self, stats):
        self.stats = stats # reference
        super(ExceptionStatsLogger, self).__init__()
        self.setLevel(logging.ERROR)

    def emit(self, record):
        errors = self.stats.get_value('logging/errors')
        try:
            # If this exception was raised in a pipeline, the item will be included in args
            url = record.args['item']['url']
        except KeyError:
            url = 'unknown url'

        msg = "{0}: {1}".format(record.exc_info[0].__name__, record.exc_info[1])
        items = errors.get(msg, [])
        items.append(url)
        errors[msg] = items

        self.stats.set_value('logging/errors', errors)


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

def normalize_price(string):
    """
    Currenlty replaces commas with decimals in currency

    Converts u"$19,99" -> u"$19.99"
    """
    return string.replace(",",".")

def extract_decimal(string):
        """
        Given a string, returns a Decimal

        Ie: u'$19.99' -> Decimal('19.99')
        """
        num = ''.join(i for i in string if i in "0123456789.")
        return decimal.Decimal(num)

def extract_currency(string):
        """
        Given a string, returns everything that wasn't a number, less whitespace

        Ie: u'$19.99' -> '$'
            u'$100CAD' -> '$CAD'
        """
        pattern = re.compile(r'[0-9\s\.]')
        currency = re.sub(pattern, '', string)
        return currency

def sanitize_html(html):
    allowed_tags = ['div', 'ul', 'ol', 'li', 'p', ]
    allowed_attrs = {
        '*': [],
    }
    return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs,
                        strip=True)

