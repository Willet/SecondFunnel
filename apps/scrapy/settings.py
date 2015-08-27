# Scrapy settings for scraper project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

import os
from django.conf import settings

BOT_NAME = 'scraper'

SPIDER_MODULES = ['apps.scrapy.spiders']
NEWSPIDER_MODULE = 'apps.scrapy.spiders'

EXTENSIONS = {
    # SentrySignals removed because we don't use Sentry.
    # See utils.extensions file for more info.
    #'apps.scrapy.utils.extensions.SentrySignals': 10,

    'apps.scrapy.logging.signals.Signals': 10,
}

# Image storage information here:
#   http://doc.scrapy.org/en/latest/topics/images.html#images-storage
# Even though this isn't used, it is still required :S
IMAGES_STORE = '/Users/nterwoord/Code/ScrapyExperiment'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# surlatable.com, err, blocks spiders
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1944.0 Safari/537.36'

# SENTRY_DSN = 'http://be7092f5a43648119e03e77ec002caff:7739e5e90d1b4f1da99ef8db9ba1ca2b@app.getsentry.com/22626'

# Complete list of signals: http://doc.scrapy.org/en/latest/topics/signals.html
# SENTRY_SIGNALS = [
#     'item_dropped',
#     'spider_error'
# ]

AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY

import cloudinary
cloudinary.config(**settings.CLOUDINARY)
