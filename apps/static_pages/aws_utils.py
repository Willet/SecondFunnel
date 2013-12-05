"""
S3 and Route53 helpers
"""

import re
import functools
import StringIO
import gzip

from django.conf import settings

from boto import sns

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from boto.route53.connection import Route53Connection
from boto.route53.record import ResourceRecordSets
from boto.route53.exception import DNSServerError

from apps.static_pages.decorators import connection_required, get_connection


# Source: http://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region
# Currently not accessible via APIs
S3_WEBSITE_HOSTED_ZONE_IDS = {
    's3-website-us-east-1.amazonaws.com': 'Z3AQBSTGFYJSTF',
    's3-website-us-west-2.amazonaws.com': 'Z3BJ6K6RIION7M',
    's3-website-us-west-1.amazonaws.com': 'Z2F56UZL2M1ACD',
    's3-website-eu-west-1.amazonaws.com': 'Z1BKCTXD74EZPE',
    's3-website-ap-southeast-1.amazonaws.com': 'Z3O0J2DXBE1FTB',
    's3-website-ap-southeast-2.amazonaws.com': 'Z1WCIGYICN2BYD',
    's3-website-ap-northeast-1.amazonaws.com': 'Z2M4EHUR26P7ZW',
    's3-website-sa-east-1.amazonaws.com': 'Z7KQH4QJS55SO',
    's3-website-us-gov-west-1.amazonaws.com': 'Z31GFT0UA1I2HV'
}


@connection_required("route53")
def get_route53_change_status(change_id, conn=None):
    """
    Returns change status, or None if change is missing.
    """
    try:
        change = conn.get_change(change_id)

    # Change with provided ID does not exist
    except DNSServerError:
        return None

    else:
        return change['GetChangeResponse']['ChangeInfo']['Status']


def upload_to_bucket(bucket_name, filename, content, content_type="text/html",
    public=False, do_gzip=True):
    """
    Uploads a key to bucket, setting provided content, content type and publicity
    """
    bucket, _ = get_or_create_website_bucket(bucket_name)

    obj = Key(bucket)
    obj.key = filename
    headers = {"Content-Type": content_type}
    content = content.encode("utf-8")

    if do_gzip:
        zipr = StringIO.StringIO()

        # GzipFile doesn't support 'with', so we close it manually
        tmpf = gzip.GzipFile(filename='index.html', mode='wb', fileobj=zipr)
        tmpf.write(content)
        tmpf.close()

        content = zipr.getvalue()

        headers["Content-Encoding"] = "gzip"

    bytes_written = obj.set_contents_from_string(content, headers=headers)

    if public:
        obj.set_acl('public-read')

    return bytes_written


def get_bucket_zone_id(bucket):
    """
    Returns HostedZone ID for a given S3 Bucket.

    Docs: http://docs.aws.amazon.com/AmazonS3/latest/dev/WebsiteEndpoints.html
    """
    endpoint = bucket.get_website_endpoint()
    endpoint = endpoint.replace("{0}.".format(bucket.name), "")

    zone = S3_WEBSITE_HOSTED_ZONE_IDS.get(endpoint)

    if not zone:
        raise KeyError(
            "Unrecognized S3 Website endpoint: {0}. Consult AWS documentation"
            ".".format(
                endpoint))

    return zone, endpoint


@connection_required("route53")
def get_hosted_zone_id(zone_name, conn=None):
    """
    Looks up a hosted zone by provided name and returns its ID
    """
    zone = conn.get_hosted_zone_by_name(zone_name)
    if not zone:
        raise KeyError(
            "Could not find HostedZone with name {0}".format(zone_name))

    zoneid_match = re.match("/hostedzone/(?P<zoneid>\w+)",
        zone['GetHostedZoneResponse']['HostedZone']['Id'])

    if not zoneid_match:
        raise RuntimeError("Route53 returned unexpected HostedZone Id: {0}"
        .format(
            zone['GetHostedZoneResponse']['HostedZone']['Id']))

    return zoneid_match.group('zoneid')


@connection_required("s3")
def get_or_create_website_bucket(bucket_name, conn=None):
    """
    Gets or creates an S3 bucket by name. If created, bucket is set as public
    and configured with website hosting enabled. If bucket already exists,
    it is not modified.
    """
    new_bucket = False
    bucket = conn.lookup(bucket_name)

    if not bucket:
        # creates a new public bucket
        bucket = conn.create_bucket(bucket_name, policy='public-read')

        # set it as static website
        bucket.configure_website("index.html")

        new_bucket = True

    return bucket, new_bucket


def create_bucket_website_alias(dns_name, bucket_name=None):
    """
    Creates Route53 Alias record, mapping example.secondfunnel.com to
    an S3 website bucket at example.secondfunnel.com.{s3-regional-endpoint}

    Returns bucket, change status and change ID. Until change status is INSYNC,
    change is not live. Change ID is returned for purposes of polling for status.
    """

    # validate our input
    if not re.match("^[a-zA-Z0-9\-]+.secondfunnel.com", dns_name):
        raise ValueError("secondfunnel.com must be present in the name")

    if not bucket_name:
        bucket_name = dns_name

    zone_id = get_hosted_zone_id('secondfunnel.com.')

    bucket, _ = get_or_create_website_bucket(bucket_name)
    bucket_zone_id, bucket_endpoint = get_bucket_zone_id(bucket)

    all_changes = ResourceRecordSets(get_connection('route53'), zone_id)

    change = all_changes.add_change("CREATE", dns_name, "A")
    change.set_alias(
        alias_hosted_zone_id=bucket_zone_id,
        alias_dns_name=bucket_endpoint)

    try:
        res = all_changes.commit()

        change_info = res['ChangeResourceRecordSetsResponse']['ChangeInfo']
        return bucket, change_info['Status'], change_info['Id'].split("/")[2]

    except DNSServerError, err:
        # attempts to create duplicate records are ignored
        if not "already exists" in str(err):
            raise

        else:
            return bucket, "INSYNC", 0


def sns_connection(region_name=settings.AWS_SNS_REGION_NAME):
    """Returns an SNSConnection that is already authenticated.

    us-west-2 is oregon, the region we use by default.

    @raises IndexError
    """
    region = filter(lambda x: x.name == region_name, sns.regions())[0]
    if not region:
        raise IndexError('no such region: %s' % region_name)

    return sns.SNSConnection(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region=region)


class SNSTopic(object):
    """Object related to an Amazon SNS topic."""

    connection = None
    topic_name = ''
    arn = None  # topics have "ARNs"

    def __init__(self, topic_name=settings.AWS_SNS_TOPIC_NAME,
                 connection=None):
        """@raises IndexError"""
        if not connection:
            connection = sns_connection()

        topics_resp = connection.get_all_topics()
        arns = [topic['TopicArn'] for topic in
                topics_resp['ListTopicsResponse']['ListTopicsResult']['Topics']]
        try:
            # the correct ARN is the ARN with the topic name at the end of it
            self.arn = filter(lambda arn: topic_name in arn[-len(topic_name):],
                              arns)[0]
        except IndexError as err:
            # topic doesn't exist. make one, then get its ARN
            myself = self.create()
            self.arn = myself['CreateTopicResponse']['CreateTopicResult']\
                ['TopicArn']

        self.connection = connection
        self.topic_name = topic_name

    def publish(self, subject='', message=''):
        """Sends a message to the SNS topic.

        message may be in json form, but this function only accepts a string.
        """
        if subject is None:
            subject = ''

        if len(subject) > 100:  # max length is 100 - raise
            raise ValueError('SNS subject too long')

        if len(message) > 1024 * 256:  # max length is 256kB - raise
            raise ValueError('SNS message too long')

        self.connection.publish(topic=self.arn, message=message,
                                subject=subject)

    def create(self):
        """Creates the topic if it hasn't been created already.
        It is safe to create a topic that already exists.

        @returns {dict}

        Example return: {
            'CreateTopicResponse': {
                'ResponseMetadata': {
                    'RequestId': '4f4be027-252d-50e1-89b6-ab3dfc05fcf3'
                },
                'CreateTopicResult': {
                    'TopicArn': 'arn:aws:sns:us-west-2:056265713214:page_generator'
                }
            }
        }
        """
        return self.connection.create_topic(self.topic_name)


def sns_notify(region_name=settings.AWS_SNS_REGION_NAME,
               topic_name=settings.AWS_SNS_TOPIC_NAME,
               subject=None, message=''):
    """Sends a message to an SNS board.

    The SQS queue should subscribe to the SNS topic: http://i.imgur.com/fLOdNyD.png

    @raises all sorts of Exceptions
    """
    connection = sns_connection(region_name)
    topic = SNSTopic(topic_name=topic_name, connection=connection)
    topic.publish(subject=subject, message=message)
