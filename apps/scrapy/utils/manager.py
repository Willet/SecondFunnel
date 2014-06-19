from scrapy_webdriver.manager import WebdriverManager
from scrapy.exceptions import IgnoreRequest, NotConfigured
from scrapy_webdriver.http import WebdriverActionRequest, WebdriverRequest
from collections import deque
import copy

#
# NOTE: most of this code is copied from scrapy_webdriver project
#


class WebdriverManager(WebdriverManager):
    def __init__(self, crawler):
        super(WebdriverManager, self).__init__(crawler)
        # workaround since selenium webdriver will modify this object, so need to copy it
        self._options = copy.deepcopy(crawler.settings.get('WEBDRIVER_OPTIONS', dict()))

    def try_acquire(self, request):
        if self._lock.acquire(False):
            request.manager = self
            return request


class WebdriverSpiderMiddleware(object):
    """This middleware coordinates concurrent webdriver access attempts."""
    def __init__(self, crawler, instances):
        self.managers = []
        for i in range(instances):  # TODO: MAX PHANTOMJS BROWSERS
            self.managers.append(WebdriverManager(crawler))
        self._wait_queue = deque()
        self._wait_inpage_queue = deque()

    @classmethod
    def from_crawler(cls, crawler):
        try:
            return cls(crawler, crawler.settings.get('WEBDRIVER_INSTANCES', 1))
        except Exception as e:
            raise NotConfigured(
                'WEBDRIVER_BROWSER is misconfigured: %r (%r)'
                % (crawler.settings.get('WEBDRIVER_BROWSER'), e))

    def process_start_requests(self, start_requests, spider):
        """Return start requests, with some reordered by the manager.

        The reordering occurs as a result of some requests waiting to gain
        access to the webdriver instance. Those waiting requests are queued up
        in the manager, from which we pop the next in line after we release the
        webdriver instance while processing spider output.

        """
        return self._process_requests(start_requests, start=True)

    def process_spider_output(self, response, result, spider):
        """Return spider result, with some requests reordered by the manager.

        See ``process_start_requests`` for a description of the reordering.

        """
        for item_or_request in self._process_requests(result):
            yield item_or_request
        if isinstance(response.request, WebdriverRequest):
            # We are here because the current request holds the webdriver lock.
            # That lock was kept for the entire duration of the response
            # parsing callback to keep the webdriver instance intact, and we
            # now release it.
            response.request.manager.release(response.request.url)
            next_request = self.get_next_request()
            if next_request:
                next_request = response.request.manager.try_acquire(next_request)
                if next_request is not WebdriverRequest.WAITING:
                    yield next_request.replace(dont_filter=True)

    def get_next_request(self):
        try:
            request = self._wait_inpage_queue.popleft()
        except IndexError:
            try:
                request = self._wait_queue.popleft()
            except IndexError:
                return
        return request

    def queue_request(self, request):
        if isinstance(request, WebdriverActionRequest):
            queue = self._wait_inpage_queue
        else:
            queue = self._wait_queue
        queue.append(request)

    def _process_requests(self, items_or_requests, start=False):
        """Acquire the webdriver manager when it's available for requests."""
        error_msg = "WebdriverRequests from start_requests can't be in-page."
        for request in iter(items_or_requests):
            if isinstance(request, WebdriverRequest):
                if start and isinstance(request, WebdriverActionRequest):
                    raise IgnoreRequest(error_msg)

                # check each manager, seeing if we can use it
                for manager in self.managers:
                    try_request = manager.try_acquire(request)
                    if try_request:
                        request = try_request
                        break
                if not try_request:
                    self.queue_request(request)
                    request = None
                if request is WebdriverRequest.WAITING:
                    continue  # Request has been enqueued, so drop it.
            yield request
