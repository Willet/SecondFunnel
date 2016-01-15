import random

from django.core.management.base import BaseCommand
from optparse import make_option

from apps.assets.models import Page, Product, ProductImage
from apps.imageservice.utils import get_filetype
from apps.scrapy.spiders.datafeeds.legacy import find_datafeed
from apps.scrapy.log import notify_slack, upload_to_s3

# Required to use scrapy logging
class FakeSpider(object):
    """ Emulte spider keys """
    def __init__(self, name, page_name):
        self.name = name
        self.reporting_name = "page {}".format(page_name.upper())


class FakeLog(object):
    def getvalue(self):
        return ""


class Command(BaseCommand):
    help = """Updates products from a product data feed

    NOTE: Deprecated in favor of update_page
    
    Usage:
    python manage.py datafeed_update <url_slug>

    -s, --similar-products
        Generate similar product recommendations

    url_slug
        Url slug of the page to update
    """
    option_list = BaseCommand.option_list + (
            make_option('-s','--similar-products',
                action="store_true",
                dest="similar_products",
                default=False,
                help="Generate similar product recommendations."),
        )

    def handle(self, url_slug, **options):
        page = Page.objects.get(url_slug=url_slug)
        store = page.store
        opts = {
            'similar_products': options['similar_products'],
        }
        results = {
            'logging/errors': {},
            'logging/items dropped': {'match failed': []},
            'logging/items out of stock': [],
            'logging/items updated': [],
            'logging/new items': [],
            'log': FakeLog(),
        }

        # Initialize Product Data Feed
        datafeed = find_datafeed(store.slug)()
        datafeed.load(opts)

        products = page.feed.get_all_products() # returns QuerySet
        print u"Found {} products for {}".format(products.count(), url_slug)

        # Find product in product data feed & update
        for product in products.iterator():
            match = field = val = None
            try:
                match = datafeed.lookup_product(product)
            except Exception as e:
                errors = results['logging/errors']
                msg = '{}: {}'.format(e.__class__.__name__, e)
                items = errors.get(msg, [])
                items.append(product.url)
                errors[msg] = items
                results['logging/errors'] = errors
                print 'logging/errors: {}'.format(msg)
            else:
                data, field = match
                if data:
                    # Found matching product
                    print u"{} match: {}".format(field, product.url)

                    datafeed.update_product(product, data)
                    product.save()

                    if product.in_stock:
                        results['logging/items updated'].append(product.url)
                    else:
                        results['logging/items out of stock'].append(product.url)
                else:
                    print u"\tMatch FAILED: {} {}".format(product.name.encode('ascii', errors='ignore'), product.url)
                    # Out of stock items often just disappear from the feeds
                    if product.in_stock:
                        product.in_stock = False
                        product.save()
                        # If an item just switched, record it that way
                        results['logging/items out of stock'].append(product.url)
                    else:
                        # If the item previously was out of stock, call it dropped
                        results['logging/items dropped']['match failed'].append(product.url)

        print "Updates saved"

        spider = FakeSpider("{} Datafeed".format(store.name), url_slug)
        reason = "finished"

        # Save results
        summary_url, log_url = upload_to_s3.S3Logger(
            results,
            spider,
            reason
        ).run()

        notify_slack.dump_stats(
            results,
            spider,
            reason,
            (summary_url, log_url)
        )
