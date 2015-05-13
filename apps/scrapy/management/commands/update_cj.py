from django.core.management.base import BaseCommand
from django.db import transaction
from optparse import make_option

from apps.assets.models import Page, Product
from apps.scrapy.datafeed.cj import download_product_datafeed, load_product_datafeed, delete_product_datafeed
from apps.scrapy.logging import notify_slack, upload_to_s3

# Required to use scrapy logging
class FakeSpider(object):
    """ Emulte spider keys """
    def __init__(self, name):
        self.name = name


class FakeLog(object):
    def getvalue(self):
        return ""


class Command(BaseCommand):
    help = """Updates products from a CJ product data feed
    Usage:
    python manage.py update_cj <url_slug>

    url_slug
        Url slug of the page to update
    """
    @staticmethod
    def update_product(product, data, results):
        product.price = float(data['PRICE'])
        product.sale_price = float(data['SALEPRICE'])
        product.in_stock = True if data['INSTOCK'] == 'yes' else False
        product.attributes['cj_link'] = data['BUYURL']
        product.save()

        if not product.in_stock:
            results['logging/items out of stock'].append(product.url)
            #print 'logging/items out of stock: {}'.format(product.url)
        else:
            results['logging/items updated'].append(product.url)
            #print 'logging/items updated: {}'.format(product.url)

    
    def handle(self, url_slug, **options):
        page = Page.objects.get(url_slug=url_slug)
        results = {
            'logging/errors': {},
            'logging/items dropped': [],
            'logging/items out of stock': [],
            'logging/items updated': [],
            'logging/new items': [],
            'log': FakeLog(),
        }

        # Grab CJ Product Data Feed
        product_datafeed_filename = download_product_datafeed(page.store)

        # Import data feed & generate lookup table
        lookup_table = load_product_datafeed(filename=product_datafeed_filename,
                                             collect_fields=["SKU", "NAME", "DESCRIPTION", "PRICE",
                                                             "SALEPRICE", "BUYURL", "INSTOCK"],
                                             lookup_fields=["SKU","NAME"])
        try:
            products = page.feed.get_all_products()
            print u"Found {} products for {}".format(len(products), url_slug)

            # Find product in product data feed & update
            with transaction.atomic():
                for product in products:
                    try:
                        try:
                            data = lookup_table["SKU"][product.sku]
                            if data:
                                print u"SKU match: {}".format(product.url)
                                self.update_product(product, data, results)
                        except KeyError:
                            try:
                                data = lookup_table["NAME"][product.name.encode('ascii', errors='ignore')]
                                if data:
                                    print u"NAME match: {}".format(product.url)
                                    self.update_product(product, data, results)
                            except KeyError:
                                print u"\tMatch FAILED: {} {}".format(product.name.encode('ascii', errors='ignore'), product.url)
                                # TODO: attempt fuzzy DESCRIPTION matching?
                                results['logging/items dropped'].append(product.url)
                    except Exception as e:
                        errors = results['logging/errors']
                        msg = '{}: {}'.format(e.__class__.__name__, e)
                        items = errors.get(msg, [])
                        items.append(product.url)
                        errors[msg] = items
                        results['logging/errors'] = errors
                        print 'logging/errors: {}'.format(msg)

            print "Updates saved"

            spider = FakeSpider("CJ Sur La Table Mothersday")
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
        finally:
            # Whatever happened, delete the file
            delete_product_datafeed(product_datafeed_filename)
