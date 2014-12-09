from datetime import datetime
import json

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from django.conf import settings

BUCKET_NAME = 'scrapy.secondfunnel.com'
DOMAIN = BUCKET_NAME + '.s3.amazonaws.com/'

class S3Logger(object):
    def __init__(self, stats, spider, reason):
        self.conn = S3Connection(
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY
        )
        self.bucket = self.conn.get_bucket(BUCKET_NAME)
        self.key = Key(self.bucket)

        self.stats = stats
        self.spider = spider
        self.reason = reason


    def run(self):
        report_url = self.send_summary()
        log_url = self.send_log()
        return report_url, log_url


    def _generate_filename(self, type):
        # path format: <environment>/<spider>/<type>/<datetime>[/(some number)]
        env = settings.ENVIRONMENT
        spider = self.spider.name
        filename = datetime.now().strftime('%Y-%m-%d,%H:%M:%S.%f')

        # validate the name is unique
        return '/'.join([env, spider, type, filename])

    def send_log(self):
        self.key.key = self._generate_filename('log')
        self.key.content_type = "text/text"
        self.key.set_contents_from_string(self.stats.get('log').getvalue())

        return DOMAIN + self.key.key


    def send_summary(self):
        self.key.key = self._generate_filename('summary')
        self.key.content_type = "text/json"
        self.key.set_contents_from_string(self._format_report())

        return DOMAIN + self.key.key


    def _format_report(self):
        report = {
            'spider': self.spider.name,
            'scrape-status': self.reason,

            'errors': self.stats.get('logging/errors', {}),
            'dropped items': self.stats.get('logging/items dropped', []),
            'out of stock': self.stats.get('logging/items out of stock', []),
            'new items': self.stats.get('logging/new items', []),
            'updated items': self.stats.get('logging/items updated', []),
        }

        return json.dumps(report, indent=4, separators=(',', ': '))
