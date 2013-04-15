import functools

from django.conf import settings

from boto.route53.connection import Route53Connection
from boto.s3.connection import S3Connection


S3_SERVICE_CLASSES = {
    's3': S3Connection,
    'route53': Route53Connection
}


def get_connection(service):
    """
    Returns an appropriate connection object.
    """
    service_class = S3_SERVICE_CLASSES.get(service)

    if not service_class:
        raise ValueError(
            "Connection to service not supported: {0}".format(service))

    return service_class(aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)


def connection_required(service_class):
    """
    Decorator that ensures passed in connection is of correct type,
    or creates a connection if none was passed in.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            proper_conn = S3_SERVICE_CLASSES.get(service_class)
            if not proper_conn:
                raise TypeError("Service class not recognized: {0}".format(
                    service_class))

            conn = kwargs.get("conn")
            # connection was passed in
            if conn:
                if not isinstance(conn, proper_conn):
                    raise TypeError("Trying to use wrong connection type")

            else:
                kwargs.update({
                    'conn': get_connection(service_class)
                })

            return func(*args, **kwargs)
        return wrapper
    return decorator
