import re

from django.conf import settings
from storages.backends.s3boto import S3BotoStorage

AWS_EXPIRES_REGEXES = getattr(settings, 'AWS_EXPIRES_REGEXES', [])


class CustomExpiresS3BotoStorage(S3BotoStorage):
    """
    S3 storage backend that allows different expiry times for different files through the use of regexes.
    The AWS_EXPIRES_REGEXES setting should be a list of tuples of the form [(regexp_string, expiry_time), ..]
    """
    def __init__(self, *args, **kwargs):
        super(CustomExpiresS3BotoStorage, self).__init__(*args, **kwargs)
        self.expires_regexes = self.__compile_regexes(AWS_EXPIRES_REGEXES)

    def __compile_regexes(self, regexes):
        return map(lambda x: (re.compile(x[0]), x[1]), regexes)

    """
    Overrides the default url generator to apply given expiry times to matching regexes
    Based on source code in storages.backends.s3boto.S3BotoStorage
    """
    def url(self, name):
        name = self._normalize_name(self._clean_name(name))
        if self.custom_domain:
            return "%s://%s/%s" % ('https' if self.secure_urls else 'http',
                                   self.custom_domain, name)
        for (regex, expiry) in self.expires_regexes:
            if regex.search(name) is not None:
                return self.connection.generate_url(expiry,
                    method='GET', bucket=self.bucket.name, key=self._encode_name(name),
                    query_auth=self.querystring_auth, force_http=not self.secure_urls)
        return self.connection.generate_url(self.querystring_expire,
            method='GET', bucket=self.bucket.name, key=self._encode_name(name),
            query_auth=self.querystring_auth, force_http=not self.secure_urls)
