from datetime import datetime
import json

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from django.conf import settings

def connect():
    conn = S3Connection(
        settings.AWS_ACCESS_KEY_ID,
        settings.AWS_SECRET_ACCESS_KEY
    )
    bucket = conn.get_bucket('scrapy.secondfunnel.com')
    key = Key(bucket)

    return bucket, key

def generate_public_id(ext):
    name = datetime.now().strftime('%Y-%m-%d,%H:%M')
    return '.'.join([name, ext])


def full_log(log, spider):
    bucket, key = connect()
    key.key = '/'.join([settings.ENVIRONMENT, spider.name, 'full-log', generate_public_id('log')])
    key.content_type = "text/text"
    key.set_contents_from_string(log)

    return 'http://' + bucket.name + '.s3.amazonaws.com/' + key.key

def general_report(stats, spider, reason):
    bucket, key = connect()
    key.key = '/'.join([settings.ENVIRONMENT, spider.name, 'report', generate_public_id('report')])
    key.content_type = "text/json"

    report = {}

    report['spider'] = spider.name
    report['date/time'] = datetime.now().isoformat('+')
    report['scrape-status'] = reason

    report['errors'] = stats.get('errors', {})
    report['dropped items'] = stats.get('dropped_items', [])
    report['out of stock'] = stats.get('out_of_stock', [])
    report['new items'] = stats.get('new_items', [])
    report['updated items'] = stats.get('updated_items', [])

    key.set_contents_from_string(json.dumps(report, indent=4, separators=(',', ': ')))

    return 'http://' + bucket.name + '.s3.amazonaws.com/' + key.key
