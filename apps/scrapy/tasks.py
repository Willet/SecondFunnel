import json
import urlparse

from celery import Celery
from django.conf import settings
from importlib import import_module
from twisted.internet import reactor

from scrapy import log as scrapy_log, signals
from scrapy.crawler import Crawler
from scrapy.settings import CrawlerSettings
from scrapy.utils.project import get_project_settings

from apps.assets.models import Page

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
celery = Celery()

@celery.task
def scrape_task(category, start_urls, create_tiles, page_slug, session_key, job_id):
    page = Page.objects.get(url_slug=page_slug)
    feeds = [page.feed.id] if create_tiles else []
    opts = {
        'recreate_tiles': False,
        'skip_images': False,
        'skip_tiles': not create_tiles,
    }

    # set up standard framework for running spider in a script
    settings = get_project_settings()
    crawler = Crawler(settings)
    crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
    crawler.configure()

    spider = crawler.spiders.create(page.store.slug, **opts)
    spider.start_urls = start_urls
    spider.categories = [category] if category else []
    spider.feed_ids = feeds

    crawler.crawl(spider)
    scrapy_log.start()
    scrapy_log.msg(u"Starting spider with options: {}".format(opts))
    crawler.start()

    reactor.run(installSignalHandlers=False)

    # Update session with results
    session = SessionStore(session_key=session_key)
    session['jobs'][job_id].update({
        'complete': True,
        'log_url': crawler.stats.get_value('log_url', ''),
        'summary_url': crawler.stats.get_value('summary_url', ''),
        'summary': crawler.stats.get_value('summary', ''),
    })
    session.save()
