from boto.s3.connection import S3Connection
from boto.s3.key import Key

conn = S3Connection(
    self.crawler.settings.get('AWS_ACCESS_KEY_ID'), 
    self.crawler.settings.get('AWS_SECRET_ACCESS_KEY')
)
bucket = conn.get_bucket('scrapy.secondfunnel.com')

key = Key(bucket)
key.key = settings.ENVIRONMENT + '/'
key.set_contents_as_string(self.fake_log.str)

# TODO:
# blah blah blah
