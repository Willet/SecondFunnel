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

from apps.assets.models import Page, Product, Tile

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
celery = Celery()

@celery.task(bind=True, ignore_result=True, max_retries=1)
def scrape_task(self, category, start_urls, no_priorities, create_tiles, page_slug, job_id, session_key=False):
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
    if (session_key):
        session = SessionStore(session_key=session_key)
        try:
            session['jobs'][job_id].update({
                'complete': no_priorities,
                'log_url': crawler.stats.get_value('log_url', ''),
                'summary_url': crawler.stats.get_value('summary_url', ''),
                'summary': crawler.stats.get_value('summary', ''),
            })
            session.save()
        except KeyError:
            pass

@celery.task(bind=True, ignore_result=True, max_retries=1)
def prioritize_task(self, start_urls, priorities, job_id, session_key=False):
    if len(priorities) > 0:
        summaryText = u"\n\n<b>--- PRIORITIES ---</b>\n\n"
        for i, url in enumerate(start_urls):
            prods = Product.objects.filter(url=url)
            for prod in prods:
                summaryText += u"- Updated tiles for <b>{}</b> with priority <b>{}</b>:\n".format(prod, priorities[i])
                for tile in prod.tiles.all():
                    tile.priority = priorities[i]
                    tile.save()
                    summaryText += u"    * <b>{}</b>\n".format(tile)
            summaryText += u"<a href='{}'>{}</a>\n".format(url, url)

        if (session_key):
            session = SessionStore(session_key=session_key)
            try:
                session_job = session['jobs'][job_id]
                summaryText = session_job['summary'] + summaryText
                session_job.update({
                    'complete': True,
                    'summary': summaryText,
                })
                session.save()
            except KeyError:
                pass
