import os
import logging

from django.conf import settings
from django.utils.encoding import force_text
from django.views.debug import ExceptionReporter, get_exception_reporter_filter

from .slack_broadcast import msg as slack_msg

class AdminSlackHandler(logging.Handler):
    """An exception log handler that sends log entries to Slack.

    If the request is passed as the first argument to the log record,
    request data will be provided in the email report.
    """
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        try:
            request = record.request
            subject = '%s (%s IP): %s' % (
                record.levelname,
                ('internal' if request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS
                 else 'EXTERNAL'),
                record.getMessage()
            )
            filter = get_exception_reporter_filter(request)
            request_repr = '\n{}'.format(force_text(filter.get_request_repr(request)))
        except Exception:
            subject = '%s: %s' % (
                record.levelname,
                record.getMessage()
            )
            request = None
            request_repr = "unavailable"

        if record.exc_info:
            exc_info = record.exc_info
        else:
            exc_info = (None, record.getMessage(), None)

        if settings.ENVIRONMENT == 'dev' and getattr(settings,'SLACK_USERNAME', False):
            channel = '@{}'.format(settings.SLACK_USERNAME)
        else:
            channel="#servers"

        title = "{} Server".format(os.getenv("AWS_GROUP", "Dev"))
        message = "%s\n\nRequest repr(): %s" % (self.format(record), request_repr)

        slack_msg(channel=channel, sender="django", title=title, message=message, level="error")
