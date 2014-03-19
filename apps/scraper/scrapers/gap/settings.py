SPIDER_MODULES = ['apps.scraper.scrapers.gap.spiders']
NEWSPIDER_MODULE = 'apps.scraper.scrapers.gap.spiders'
DEFAULT_ITEM_CLASS = 'apps.scraper.scrapers.gap.items.GapProductItem'

ITEM_PIPELINES = ['apps.scraper.scrapers.gap.pipelines.GapProductPipeline']