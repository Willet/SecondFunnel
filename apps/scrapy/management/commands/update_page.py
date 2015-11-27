from django.core.management.base import BaseCommand
from optparse import make_option

from apps.assets.models import Page
from apps.scrapy.controllers import PageMaintainer


class Command(BaseCommand):
    help = """Updates all products in a given page.
    Usage:
    python manage.py update_page [-t, --recreate-tiles] [-i, --update-images] [-s, scrape] <url_slug>

    url_slug
        Url slug of the page to rescrape

    -t, --recreate_tiles
        Recreate tiles the already exist.  Useful for removing out-dated associations & data.

    -i, --update-images
        Scrape product images.
    """
    option_list = BaseCommand.option_list + (
            make_option('-t','--recreate-tiles',
                action="store_true",
                dest="recreate_tiles",
                default=False,
                help="Recreate all tiles."),
            make_option('-i','--update-images',
                action="store_true",
                dest="update_images",
                default=False,
                help="Scrape product images."),
            make_option('-s','--scrape',
                action="store_true",
                dest="scrape",
                default=False,
                help="Use page scraper."),
        )

    def handle(self, url_slug, **options):
        page = Page.objects.get(url_slug=url_slug)
        PageMaintainer(page).update(options={
            'recreate_tiles': options['recreate_tiles'],
            'skip_images': not options['update_images'],
            'skip_tiles': True,
            'project': 'pages' if options['scrape'] else 'datafeeds',
        })
        
