import httplib2

from os import path

def read_a_file(file_name, default_value=''):
    """just a file opener with a catch."""
    try:
        with open(path.abspath(file_name)) as f:
            return f.read()
    except (IOError, TypeError):
        return default_value


def read_remote_file(url, default_value=''):
    """just a url opener with a catch."""
    try:
        h = httplib2.Http()
        response, content = h.request(url)
        if not 200 <= int(response.status) <= 300:
            return default_value

        return content
    except (ValueError, httplib2.RelativeURIError) as err:
        return default_value
