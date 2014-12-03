from scrapy import signals, log
from django.conf import settings

import notify_hipchat
import upload_to_s3

class LogListener(object):
    """
    Record all logging from spiders.
    LogListener objects pretend to be file objects by implementing a "write" and 
    a "close" method.  They can then be used by ScrapyFileLogObserver.
    """
    def __init__(self):
        self.str = ""
    def write(self, string):
        self.str += string
    def flush(self):
        pass
    def close(self):
        pass


class Signals(object):
    """
    Record progress of spider for use in logging, using scrapy signal hooks.
    This is actually an extension: http://doc.scrapy.org/en/latest/topics/extensions.html
    Details on signal hooks: http://doc.scrapy.org/en/latest/topics/signals.html

    Scrapy docs are disorganized, this page gives details of the crawler object:
    http://doc.scrapy.org/en/latest/topics/api.html
    """
    fake_log = LogListener()

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
        log.ScrapyFileLogObserver(self.fake_log, level=log.DEBUG).start()


    def item_scraped(self, item, response, spider):
        # inc_value uses the + operator!  The __add__ method of lists
        # performs list concatenation.
        # The other methods of this class use the long approach because
        # dicts don't have an __add__ method.
        self.crawler.stats.inc_value('new_items' if item['created'] else 'updated_items', [item['url']],[])
        if not item.get('in_stock', True):
            self.crawler.stats.inc_value('out_of_stock', [item['url']], [])


    def item_dropped(self, item, spider, exception):
        dropped_items = self.crawler.stats.get_value('dropped_items', {})

        msg = str(exception).split(':')[0]
        items = dropped_items.get(msg, [])
        items.append('url: {}'.format(item.get('url', "(?)")))
        dropped_items[msg] = items

        self.crawler.stats.set_value('dropped_items', dropped_items)


    def spider_error(self, failure, response, spider):
        errors = self.crawler.stats.get_value('errors', {})

        msg = failure.getErrorMessage()
        items = errors.get(msg, [])
        items.append('url: {}'.format(response.url))
        errors[msg] = items

        self.crawler.stats.set_value('errors', errors)


    def spider_closed(self, spider, reason):
        if settings.ENVIRONMENT == 'dev':
            pass # return

        full_log = upload_to_s3.full_log(self.fake_log.getvalue(), spider)
        report = upload_to_s3.general_report(self.crawler.stats.get_stats(), spider, reason)

        notify_hipchat.dump_stats(self.crawler.stats.get_stats(), spider, reason, (report, full_log))
