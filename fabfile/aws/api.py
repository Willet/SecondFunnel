import boto
import boto.ec2
from secondfunnel.settings import common as django_settings
from utils import flatten_reservations


def get_ec2_connection():
    return boto.ec2.connect_to_region(
        "us-west-2",
        aws_access_key_id=django_settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=django_settings.AWS_SECRET_ACCESS_KEY
    )


def get_instances(name):
    ec2 = get_ec2_connection()
    res = ec2.get_all_instances(filters={'tag:Name': name})

    # we only want running instances
    return [i for i in flatten_reservations(res) if i.state in ['running', 'pending']]
