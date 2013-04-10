"""
S3 and Route53 helpers
"""

import re
import functools

from django.conf import settings

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
    public=False):
    """
    Uploads a key to bucket, setting provided content, content type and publicity
    """
    bucket, _ = get_or_create_website_bucket(bucket_name)

    obj = Key(bucket)
    obj.key = filename
    bytes_written = obj.set_contents_from_string(
        content.encode("utf-8"),
        headers={"Content-Type": content_type}
    )
    if public:
        obj.set_acl('public-read')

    return bytes_written


def get_bucket_zone_id(bucket):
    """
    Returns HostedZone ID for a given S3 Bucket.

    Docs: http://docs.aws.amazon.com/AmazonS3/latest/dev/WebsiteEndpoints.html
    """
    endpoint = bucket.get_website_endpoint()
    endpoint = endpoint.replace("{}.".format(bucket.name), "")

    zone = S3_WEBSITE_HOSTED_ZONE_IDS.get(endpoint)

    if not zone:
        raise KeyError(
            "Unrecognized S3 Website endpoint: {}. Consult AWS documentation.".format(
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
            "Could not find HostedZone with name {}".format(zone_name))

    zoneid_match = re.match("/hostedzone/(?P<zoneid>\w+)",
        zone['GetHostedZoneResponse']['HostedZone']['Id'])

    if not zoneid_match:
        raise RuntimeError("Route53 returned unexpected HostedZone Id: {}".format(
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


def create_bucket_website_alias(desired_name):
    """
    Creates Route53 Alias record, mapping example.secondfunnel.com to
    an S3 website bucket at example.secondfunnel.com.{s3-regional-endpoint}

    Returns bucket, change status and change ID. Until change status is INSYNC,
    change is not live. Change ID is returned for purposes of polling for status.
    """

    # validate our input
    if not re.match("^[a-zA-Z0-9\-]+.secondfunnel.com", desired_name):
        raise ValueError("secondfunnel.com must be present in the name")

    zone_id = get_hosted_zone_id('secondfunnel.com.')

    bucket, _ = get_or_create_website_bucket(desired_name)
    bucket_zone_id, bucket_endpoint = get_bucket_zone_id(bucket)

    all_changes = ResourceRecordSets(get_connection('route53'), zone_id)

    change = all_changes.add_change("CREATE", desired_name, "A")
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
