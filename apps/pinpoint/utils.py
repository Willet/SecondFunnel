import gzip
import urllib2
import StringIO

from os import path

def read_a_file(file_name, default_value=''):
    """just a file opener with a catch."""
    try:
        with open(path.abspath(file_name)) as f:
            return f.read()
    except (IOError, TypeError):
        return default_value


def read_remote_file(url, default_value=''):
    """
    Url opener that reads a url and gets the content body.
    Returns a tuple response where the first item is the data and the
    second is whether the response was gzipped or not.
    """
    try:
        request = urllib2.Request(url)
        request.add_header('Accept-encoding', 'gzip')
        # in case Python-urllib/2.6 would be rejected
        request.add_header('User-agent', 'Mozilla/5.0')
        response = urllib2.urlopen(request)

        if not 200 <= int(response.getcode()) <= 300:
            return default_value, False

        if response.info().get('Content-Encoding') == 'gzip':
            buf = StringIO.StringIO(response.read())
            zfile = gzip.GzipFile(fileobj=buf)
            content = zfile.read()
            zfile.close()
            return content, True

        content = response.read()
        return content, False
    except (TypeError, ValueError, urllib2.HTTPError) as err:
        return default_value, False
