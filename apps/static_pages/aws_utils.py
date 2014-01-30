"""
S3 and Route53 helpers
"""

import gzip
import json
import re
import StringIO

from functools import partial
from django.conf import settings

from boto import sns
from boto import sqs
from boto.sqs.message import RawMessage

from boto.s3.key import Key

from boto.route53.record import ResourceRecordSets
from boto.route53.exception import DNSServerError
import sys

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


@connection_required("s3")
def download_from_bucket(bucket_name, filename, conn=None):
    """:return file contents

    """
    bucket = conn.lookup(bucket_name)
    if not bucket:
        raise ValueError("Bucket {0} not found".format(bucket_name))


@connection_required("s3")
def copy_across_bucket(source_bucket_name, dest_bucket_name, filename,
                       overwrite=False, conn=None):
    source_bucket = conn.get_bucket(source_bucket_name)
    dest_bucket = conn.get_bucket(dest_bucket_name)

    key = source_bucket.get_key(filename)

    if not dest_bucket.get_key(filename) or overwrite:
        try:
            key.copy(dest_bucket_name, filename)
            print "Copy Success : %s" % filename
        except:
            print "Copy Error: %s" % sys.exc_info()
    else:
        raise IOError("Key Already Exists, will not overwrite.")


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

    return sns.SNSConnection(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region=region)


def sqs_connection(region_name=settings.AWS_SQS_REGION_NAME):
    """Returns an SQSConnection that is already authenticated.

    us-west-2 is oregon, the region we use by default.

    @raises IndexError
    """
    region = filter(lambda x: x.name == region_name, sqs.regions())[0]

    return sqs.connect_to_region(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=region_name)


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

        self.connection = connection
        self.topic_name = topic_name

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

        return self.connection.publish(topic=self.arn, message=message,
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


class SQSQueue(object):
    """Object related to an Amazon SQS queue."""

    connection = None
    queue = None

    def __init__(self, queue_name=settings.AWS_SQS_QUEUE_NAME,
                 connection=None):
        """."""
        if not connection:
            connection = sqs_connection()

        self.connection = connection
        # @type {boto.sqs.queue.Queue}
        self.queue = connection.get_queue(queue_name=queue_name)
        if not self.queue:
            raise ValueError('Error retrieving queue {0}'.format(queue_name))
        self.queue.set_message_class(RawMessage)

    def receive(self, num_messages=1):
        """Retrieve one message from the SQS queue.

        SQS Queues have visibility timeouts.
        Repeated calls may receive different messages.

        @returns {list}  [<boto.sqs.message.Message instance]
        """
        try:
            return self.queue.get_messages(num_messages=num_messages)
        except BaseException as err:  # both appear to work the same, so if one fails, do the other
            return self.connection.receive_message(self.queue,
                                                   number_messages=num_messages)

    def write_message(self, data):
        """Writes a JSON-encoded string to the queue."""
        message = RawMessage()
        message.set_body(json.dumps(data))

        return self.queue.write(message)

    def delete_message(self, message):
        return self.queue.delete_message(message=message)


def sns_notify(region_name=settings.AWS_SNS_REGION_NAME,
               topic_name=settings.AWS_SNS_TOPIC_NAME,
               subject=None, message='', dev_suffix=False):
    """Sends a message to an SNS board.

    The SQS queue should subscribe to the SNS topic: http://i.imgur.com/fLOdNyD.png

    @param dev_suffix {bool} whether '-dev' or '-test' will be added to the
    topic name depending on the current environment.

    @raises {IndexError|TypeError|ValueError}
    """

    # ENVIRONMENT is "production" in production
    if dev_suffix and settings.ENVIRONMENT in ['dev', 'test']:
        topic_name = '{topic_name}-{env}'.format(topic_name=topic_name,
                                                 env=settings.ENVIRONMENT)

    connection = sns_connection(region_name)
    topic = SNSTopic(topic_name=topic_name, connection=connection)
    return topic.publish(subject=subject, message=message)


def sqs_poll(callback=None, region_name=settings.AWS_SQS_REGION_NAME,
             queue_name=settings.AWS_SQS_QUEUE_NAME, dev_suffix=False):
    """accept messages from a sqs queue, then pass it into callback.

    If callback is given, run callback on messages. Otherwise, return messages.

    @returns {list}
    """

    # ENVIRONMENT is "production" in production
    if dev_suffix and settings.ENVIRONMENT in ['dev', 'test']:
        queue_name = '{queue_name}-{env}'.format(queue_name=queue_name,
                                                 env=settings.ENVIRONMENT)

    connection = sqs_connection(region_name=region_name)

    queue = SQSQueue(queue_name=queue_name, connection=connection)
    if not queue:
        raise ValueError('No such queue found: {0}'.format(queue_name))

    messages = queue.receive(num_messages=10)

    if not messages:
        messages = []  # default to 0 messages instead of None messages

    if callback:
        return callback(messages)

    return messages


class SNSErrorLogger(object):
    """Provides a logger object that posts logging messages to an SQS queue
    predefined in the application's environment-dependent settings.

    Available methods: log(), info(), warn(), error()
    """
    def __init__(self):
        self.info = partial(self.log, log_level="info")
        self.warn = self.warning = partial(self.log, log_level="warning")
        self.error = partial(self.log, log_level="error")

    def get_topic_name(self):
        """e.g. page-generator-queue-log-test,
                page-generator-queue-log-production
        """
        if settings.ENVIRONMENT in ['test', 'dev']:
            return '{0}-{1}'.format(settings.AWS_SNS_LOGGING_TOPIC_NAME,
                                    settings.ENVIRONMENT)
        return settings.AWS_SNS_LOGGING_TOPIC_NAME

    def get_topic_subject(self):
        """e.g. page-generator-test,
                page-generator-production
        """
        return '{0}-{1}'.format(settings.AWS_SNS_TOPIC_NAME,
                                settings.ENVIRONMENT)

    def log(self, msg, log_level="info"):
        """Publishes a message to the predefined SNS topic.

        :param log_level one of "info", "warning", and "error".
        """

        if not log_level in settings.AWS_SNS_LOGGING_LEVELS:
            raise ValueError("log_level %s not defined" % log_level)

        sns_notify(region_name=settings.AWS_SNS_REGION_NAME,
                   topic_name=self.get_topic_name(),
                   subject='{0} {1}'.format(self.get_topic_subject(), log_level),
                   message='{0}: {1}'.format(log_level.capitalize(), msg))


# import this from other modules
logger = SNSErrorLogger()
