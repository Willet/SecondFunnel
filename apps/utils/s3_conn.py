#!/usr/bin/env python

"""
S3 and Route53 helpers

reference
https://github.com/laironald/PythonBase/blob/master/messaround/route53.mess.py
"""

from django.conf import settings

try:
    import boto
    from boto.route53.connection import Route53Connection
    from boto.route53.record import ResourceRecordSets
    from boto.route53.exception import DNSServerError
    from boto.s3.connection import S3Connection
except:
    raise ImportError("Cannot import boto. "
                      "Please load a production-compatible environment.")


def get_s3_connection():
    conn = S3Connection(aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    return conn


def get_route53_connection():
    conn = Route53Connection(aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    return conn


def get_or_create_s3_bucket(conn, bucket_name):
    try:
        bucket = conn.create_bucket(bucket_name)
    except boto.exception.S3CreateError:
        bucket = conn.get_bucket(bucket_name)
    
    return bucket
    

def get_hosted_zone(conn, hosted_zone_name):
    """normalize vars"""
    hosted_zone = conn.get_hosted_zone_by_name(hosted_zone_name)
    return {'id': hosted_zone['GetHostedZoneResponse']['HostedZone']['Id'],
            'name': hosted_zone['GetHostedZoneResponse']['HostedZone']['Name']}


def get_hostedzone_simple_id(long_id):
    """/hostedzone/ZRJYRHMHTYIM6 -> ZRJYRHMHTYIM6"""
    # return '/'.join(long_id.split('/')[2:])
    return long_id.replace('/hostedzone/', '')


def get_or_create_record_set(conn, hosted_zone_obj):
    recordset = ResourceRecordSets(conn,
        hosted_zone_id=get_hostedzone_simple_id(hosted_zone_obj['id']))
    return recordset


def get_s3_hosted_zone_endpoint_id(zone_id):
    """There isn't an API for this, apparently, Fortunately, there are only
    two website hosts. So, we're going to hope that the API doesn't change.
    """
    return {
        's3-website-us-east-1.amazonaws.com': 'Z3AQBSTGFYJSTF',
        's3-website-us-west-2.amazonaws.com': 'Z3BJ6K6RIION7M',
    }[zone_id]
    

def convert_bucket_to_web_endpoint(bucket):
    """Buckets aren't web-compatible until this is enabled."""
    bucket.configure_website(suffix='index.html')
    

def get_or_create_s3_website(desired_name):
    """i.e. nativeshoes.secondfunnel.com

    get_or_create_s3_website('schiznecks.secondfunnel.com')
    """

    if not 'secondfunnel.com' in desired_name:  # well, fix it then
        desired_name = '%s.secondfunnel.com' % desired_name

    # connect
    s3_conn = get_s3_connection()
    r53_conn = get_route53_connection()
    
    # configure the bucket
    bucket = get_or_create_s3_bucket(s3_conn, desired_name)

    try:  # 2.6
        bucket.set_acl('public-read')
    except: # not 2.6 (which, apparently, makes no difference)
        pass

    convert_bucket_to_web_endpoint(bucket)

    # schiznecks.secondfunnel.com.s3-website-us-east-1.amazonaws.com
    bucket_endpoint = bucket.get_website_endpoint()
    bucket_cfg = bucket.get_website_configuration()

    # screw around with the DNS
    try:
        hosted_zone_obj = get_hosted_zone(r53_conn, 'secondfunnel.com.')

        record_set = get_or_create_record_set(r53_conn, hosted_zone_obj)

        record = record_set.add_change('CREATE', '%s.' % desired_name, 'A')
        record.set_alias(
            get_s3_hosted_zone_endpoint_id(bucket_endpoint.replace(
                '%s.' % desired_name, '')),
            bucket_endpoint.replace('%s.' % desired_name, '')
        )

        record_set.commit()
    except DNSServerError, err:
        if settings.DEBUG:
            if not 'already exists' in str(err):
                # if it's any error besides "there's already a record", show it
                raise

    return True  # this return is really just for kicks, because boto would've
                 # throw nasty errors at you anyway