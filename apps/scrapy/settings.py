# Scrapy settings for scraper project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'secondfunnel.settings.dev'

BOT_NAME = 'scraper'

SPIDER_MODULES = ['apps.scrapy.spiders']
NEWSPIDER_MODULE = 'apps.scrapy.spiders'

DOWNLOAD_HANDLERS = {
    'http': 'scrapy_webdriver.download.WebdriverDownloadHandler',
    'https': 'scrapy_webdriver.download.WebdriverDownloadHandler',
}

SPIDER_MIDDLEWARES = {
    'scrapy_webdriver.middlewares.WebdriverSpiderMiddleware': 543,
}

WEBDRIVER_BROWSER = 'PhantomJS'  # Or any other from selenium.webdriver
                                 # or 'your_package.CustomWebdriverClass'
                                 # or an actual class instead of a string.

# Optional passing of parameters to the webdriver
WEBDRIVER_OPTIONS = {
    'service_args': [
        '--debug=true', '--load-images=false', '--webdriver-loglevel=debug'
    ]
}

# http://doc.scrapy.org/en/latest/topics/item-pipeline.html#activating-an-item-pipeline-component
ITEM_PIPELINES = {
    #'scrapy.contrib.pipeline.images.ImagesPipeline': 1,
    #'apps.scrapy.pipelines.CloudinaryPipeline': 1,
    'apps.scrapy.pipelines.ValidationPipeline': 2,
    'apps.scrapy.pipelines.NamePipeline': 10,
    'apps.scrapy.pipelines.PricePipeline': 11,
    'apps.scrapy.pipelines.ForeignKeyPipeline': 997,
    'apps.scrapy.pipelines.ItemPersistencePipeline': 998,
    'apps.scrapy.pipelines.ProductImagePipeline': 999
}
# Image storage information here:
#   http://doc.scrapy.org/en/latest/topics/images.html#images-storage
# Even though this isn't used, it is still required :S
IMAGES_STORE = '/Users/nterwoord/Code/ScrapyExperiment'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'scraper (+http://www.yourdomain.com)'

import cloudinary
cloudinary.config(
    cloud_name = 'secondfunnel',
    api_key = '471718281466152',
    api_secret = '_CR94qpFu7EGChMbwmc4xqCsbXo'
)
