from django.conf import settings
import logging
from scrapy import signals

from .utils.misc import CarefulStringIO as StringIO
from .log import notify_slack, upload_to_s3


class Signals(object):
    """
    Record progress of spider for use in logging, using scrapy signal hooks.
    This is actually an extension: http://doc.scrapy.org/en/latest/topics/extensions.html
    Details on signal hooks: http://doc.scrapy.org/en/latest/topics/signals.html

    Scrapy docs are disorganized, this page gives details of the crawler object:
    http://doc.scrapy.org/en/latest/topics/api.html
    """

    @classmethod
    def from_crawler(cls, crawler):
        obj = cls()
        obj.crawler = crawler

        funcs = [func for func in dir(obj) if not func.startswith('_') and func != 'from_crawler']
        for func_name in funcs:
            func = getattr(obj, func_name)
            if not callable(func):
                continue

            signal = getattr(signals, func_name)
            if not signal:
                continue
            crawler.signals.connect(func, signal=signal)
        return obj


    def engine_started(self):
        # Save logging messages to a buffer that will be saved to S3
        log_buffer = StringIO()
        self.crawler.stats.set_value('log', log_buffer)
        formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')

        sh = logging.StreamHandler(log_buffer)
        sh.setLevel(logging.INFO)
        sh.setFormatter(formatter)

        logging.getLogger().addHandler(sh)

    def spider_opened(self, spider):
        self.crawler.stats.set_stats({
            'logging/items dropped': {},
            'logging/errors': {},
            'logging/new items': [],
            'logging/items out of stock': [],
            'logging/items updated': [],
        })


    def item_scraped(self, item, response, spider):
        # inc_value uses the + operator!  The __add__ method of lists
        # performs list concatenation.
        # The other methods of this class use the long approach because
        # dicts don't have an __add__ method.
        self.crawler.stats.inc_value('logging/new items' if item['created'] else 'logging/items updated', [item['url']],[])

        # For out-of-stock reasons other than 404 response (i.e. no images)
        # 404s should be handled by "spider_error"
        if not item.get('in_stock', True):
            self.crawler.stats.inc_value('logging/items out of stock', [item['url']], [])


    def item_dropped(self, item, spider, exception):
        msg = str(exception).split(':')[0]

        if msg == 'OutOfStock':
            self.crawler.stats.inc_value('logging/items out of stock', [item['url']], [])
        else:
            dropped_items = self.crawler.stats.get_value('logging/items dropped')
            items = dropped_items.get(msg, [])
            items.append(item.get('url'))
            dropped_items[msg] = items

            self.crawler.stats.set_value('logging/items dropped', dropped_items)


    def spider_error(self, failure, response, spider):
        errors = self.crawler.stats.get_value('logging/errors')

        msg = failure.getErrorMessage()
        items = errors.get(msg, [])
        items.append(response.url)
        errors[msg] = items

        self.crawler.stats.set_value('logging/errors', errors)


    def spider_closed(self, spider, reason):
        if settings.ENVIRONMENT == 'dev':
            pass # return

        summary_url, log_url = upload_to_s3.S3Logger(
            self.crawler.stats.get_stats(),
            spider,
            reason
        ).run()

        notify_slack.dump_stats(
            self.crawler.stats.get_stats(),
            spider,
            reason,
            (summary_url, log_url)
        )

        # to be returned to the web page
        self.crawler.stats.set_value('summary_url', summary_url)
        self.crawler.stats.set_value('log_url', log_url)
