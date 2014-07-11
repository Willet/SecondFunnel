import json
import re
import calendar
from datetime import datetime, timedelta
from urlparse import urlparse
from apps.scrapy.spiders.webdriver import SecondFunnelCrawlScraper
from apps.scrapy.utils.itemloaders import ScraperContentLoader
from apps.scrapy.items import ScraperImage, ScraperVideo
from scrapy.http import Request
from scrapy.spider import Spider


class InstagramSpider(SecondFunnelCrawlScraper, Spider):
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = []

    visited = []
    rules = []

    # http://instagram.com/p/pSNM_dqxht/ -> pSNM_dqxht
    short_id_regex = re.compile(r"/p/(.+)/$")

    def __init__(self, store_slug=None, scrape_til=None, *args, **kwargs):
        super(InstagramSpider, self).__init__(*args, **kwargs)
        # since we want to do the json parsing,
        # and they will pass the non-json urls
        self.start_urls = [url.rstrip('/') + "/media" for url in self.start_urls]
        self.store_slug = store_slug
        if store_slug is None:
            raise Exception("Store is required for Instragram Scraper,"
                            " e.g. store_slug='oldnavy'")
        if scrape_til is None:
            # default to 60 days
            time_ago = datetime.utcnow() - timedelta(days=60)
            self.scrape_til = calendar.timegm(time_ago.utctimetuple())

    def parse(self, response):
        json_body = json.loads(response.body)

        for item in json_body['items']:
            if long(item['created_time']) < self.scrape_til:
                return  # we are done
            if item['type'] == 'image':
                l = ScraperContentLoader(item=ScraperImage())
                if item['caption']:
                    l.add_value('description', item['caption']['text'])
                    l.add_value('author', item['caption']['from']['full_name'])
                else:
                    l.add_value('description', u'')
                    l.add_value('author', u'')
                l.add_value('original_url', item['link'])
                l.add_value('source', 'instagram')
                l.add_value('source_url', item['images']['standard_resolution']['url'])
                l.add_value('attributes', {'id': item['id']})
                item = l.load_item()
                yield item
            elif item['type'] == 'video':
                l = ScraperContentLoader(item=ScraperVideo())
                if item['caption']:
                    l.add_value('description', item['caption']['text'])
                    l.add_value('author', item['caption']['from']['full_name'])
                else:
                    l.add_value('description', u'')
                    l.add_value('author', u'')
                short_id = self.short_id_regex.search(item['link']).groups()[0]
                l.add_value('original_id', short_id)
                l.add_value('source', 'instagram')
                url = item['link'].replace('http:', '') + "embed/"
                l.add_value('source_url', url)
                l.add_value('attributes', {'id': item['id']})
                l.add_value('player', 'instagram')
                l.add_value('url', url)
                item = l.load_item()
                yield item

        # TODO: handle videos

        if json_body['more_available']:
            last_item = json_body['items'][-1]
            url = urlparse(response.request.url)
            next_url = "%s://%s%s?max_id=%s" % \
                (url.scheme, url.netloc, url.path, last_item['id'])
            yield Request(next_url, callback=self.parse)
