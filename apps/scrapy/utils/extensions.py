# NOT USED!!!!!
# I left this file here in case we decide to go back to using Sentry.  
# Because if we did, I would probably never find it in the git repo.
import sys

from scrapy import signals, log
from scrapy_sentry.extensions import Signals
from scrapy_sentry.utils import get_client, response_to_dict


class SentrySignals(Signals):
    """
    Have Sentry handle arbitrary scrapy signals.

    SENTRY_SIGNALS from `settings.py` controls what signals this will listen to.

    A list of available signals can be found in the docs:
        http://doc.scrapy.org/en/latest/topics/signals.html#module-scrapy.signals

    Modified from scrapy_sentry.extensions.Signals
    """
    @classmethod
    def from_crawler(cls, crawler, client=None, dsn=None):
        dsn = crawler.settings.get("SENTRY_DSN", None)
        client = get_client(dsn)
        o = cls(dsn=dsn)

        sentry_signals = crawler.settings.get("SENTRY_SIGNALS", {})

        for signal_name in sentry_signals:
            signal = getattr(signals, signal_name, None)
            receiver_fn = getattr(o, signal_name, None)

            if not (signal and receiver_fn):
                continue

            crawler.signals.connect(receiver_fn, signal=signal)

        return o

    def sentry_message(self, payload, type='message', spider=None, extra=None):
        if type == 'exception':
            result = self.client.captureException(payload, extra=extra)
        else:
            result = self.client.captureMessage(payload, extra=extra)

        cid = self.client.get_ident(result)

        logger = spider.log if spider else log.msg
        logger("Sentry ID '{}'".format(cid), level=log.INFO)

        return cid

    def spider_error(self, failure, response, spider, signal=None,
                     sender=None, *args, **kwargs):
        # Technically, `failure.value` contains the exception, but no traceback
        extra = {
            'sender': sender,
            'spider': spider.name,
            'signal': signal,
            'failure': failure,
            'response': response_to_dict(response, spider, include_request=True)
        }
        exception = sys.exc_info()

        return self.sentry_message(
            exception, type='exception', spider=spider, extra=extra
        )

    def item_dropped(self, item, spider, exception, signal=None,
                     sender=None, *args, **kwargs):
        extra = {
            'sender': sender,
            'spider': spider.name,
            'signal': signal,
            'item': item
        }

        msg = 'DropItem: {}'.format(exception.message)
        return self.sentry_message(
            msg, type='message', spider=spider, extra=extra
        )
