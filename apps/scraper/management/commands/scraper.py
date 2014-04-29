from os.path import join, dirname

from optparse import make_option
from django.core.exceptions import MultipleObjectsReturned
from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.assets.models import Store
from apps.scraper.scrapers.scraper import CloudScraper


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--store-id', default=None, dest='store-id'),
        make_option('--url', default=None),
        make_option('--folder', default=None))  # --folder is deprecated

    def handle(self, *args, **kwargs):
        """
        If called with store-id (somehow) and url, scrapes that url for
            that store.
        Otherwise, scrapes all urls listed in all text files in the urls folder.
        """
        store_id = kwargs.pop('store-id', None)
        url = kwargs.pop('url', None)
        urls_folder = kwargs.pop('folder', None)

        # allow either fields as identifiers
        try:
            store = Store.objects.get(Q(id=store_id) | Q(slug=store_id))
        except (Store.DoesNotExist, MultipleObjectsReturned) as err:
            store = None
            if store_id:  # told to scrape a store, but no such store
                raise

        # "scrape all urls for whichever store, or all stores if store is missing"
        if urls_folder:
            print "--folder option is deprecated (not useful in any way)"
        else:
            urls_folder = join(dirname(dirname(dirname(__file__))), 'urls')

        if store:  # you said scrape this store; I will scrape this store
            stores = [store]
        else:  # scrape all stores
            stores = Store.objects.all()

        urls = []
        if url:
            urls = [url]
        else:
            # scraper itinerary
            print "This multiple-scraper trip contains the URLs:"
            for store in stores:
                print store.slug
                file_name = store.slug.lower() + '.txt'
                file_link = join(urls_folder, file_name)
                try:
                    with open(file_link) as url_file:
                        for line in url_file:
                            # support comments
                            line = line.replace('\n', '')
                            if line.startswith('#'):
                                print "Skipping {0}".format(line[1:])
                                continue
                            print "- {0}".format(line)
                            urls.append(line)
                except IOError:
                    pass

        scraper = CloudScraper()
        return scraper.subscrape(urls=urls)
