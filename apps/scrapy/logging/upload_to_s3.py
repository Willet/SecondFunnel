from datetime import datetime
import json

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from django.conf import settings

class S3(object):
    def __init__(self, stats, spider, reason):
        self.conn = S3Connection(
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY
        )
        self.bucket = self.conn.get_bucket('scrapy.secondfunnel.com')
        self.key = Key(self.bucket)

        self.stats = stats
        self.spider = spider
        self.reason = reason


    def run(self):
        domain = 'http://' + self.bucket.name + '.s3.amazonaws.com/'
        return domain, self.report(), self.full_log()


    def generate_filename(self, type):
        env = settings.ENVIRONMENT
        spider = self.spider.name
        filename = datetime.now().strftime('%Y-%m-%d,%H:%M')

        return '/'.join([env, spider, type, filename])


    def full_log(self):
        self.key.key = self.generate_filename('log')
        self.key.content_type = "text/text"
        self.key.set_contents_from_string(self.stats.get('fake_log').getvalue())

        return self.key.key


    def report(self):
        self.key.key = self.generate_filename('report')
        self.key.content_type = "text/json"
        self.key.set_contents_from_string(self.format_report())

        return self.key.key


    def format_report(self):
        report = {
            'spider': self.spider.name,
            'scrape-status': self.reason,

            'errors': self.stats.get('errors', {}),
            'dropped items': self.stats.get('dropped_items', []),
            'out of stock': self.stats.get('out_of_stock', []),
            'new items': self.stats.get('new_items', []),
            'updated items': self.stats.get('updated_items', []),
        }

        return json.dumps(report, indent=4, separators=(',', ': '))
