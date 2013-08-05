import urlparse

from tastypie.serializers import Serializer


class urlencodeSerializer(Serializer):
    """
    A serializer that will allow us to do PATCH requests for supported content by
    decoding url-encoded parameters into valid JSON.
    """
    formats = ['json', 'jsonp', 'xml', 'yaml', 'html', 'plist', 'urlencode']
    content_types = {
        'json': 'application/json',
        'jsonp': 'text/javascript',
        'xml': 'application/xml',
        'yaml': 'text/yaml',
        'html': 'text/html',
        'plist': 'application/x-plist',
        'urlencode': 'application/x-www-form-urlencoded'
    }

    def from_urlencode(self, data, options=None):
        # http://stackoverflow.com/questions/14074149/
        qs = dict((k, v if len(v) > 1 else v[0] )
                  for k, v in urlparse.parse_qs(data).iteritems())
        print qs
        return qs

    def to_urlencode(self, content):
        pass


