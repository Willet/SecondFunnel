from django.core.management.base import BaseCommand
from optparse import make_option

from apps.assets.models import Page
from apps.scrapy.controllers import PageMaintainer


def get_slice_args(option, opt, value, parser):
    args = value.split(',')
    try:
        iargs = [int(a) if len(a) > 0 else None for a in args]
    except ValueError:
        raise ValueError("slice option requires integer or empty start and end arguments.")
    # Must have start and end, even if they are both None
    if len(iargs) is not 2:
        raise ValueError("slice option requires a start and end argument, separated by a comma. Either may be empty.")
    setattr(parser.values, option.dest, iargs)


class Command(BaseCommand):
    help = """Updates all products in a given page.
    Usage:
    python manage.py update_page [-t, --recreate-tiles] [-i, --update-images] [-s, scrape] <url_slug>

    url_slug
        Url slug of the page to rescrape

    -t, --recreate-tiles
        Recreate tiles the already exist.  Useful for removing out-dated associations & data.

    -i, --update-images
        Scrape product images.

    -s, --scrape
        Use page scrapers (default is use datafeed).

    -f, --fast
        Skips similar products (note: can reduce scrape time by 3x - 4x)
    -l, --slice start,end
        Update slice of products from [start:end]
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
            make_option('-f','--fast',
                action="store_true",
                dest="skip_similar_products",
                default=False,
                help="Skips similar products, can 3x improve scrape time."),
            make_option('-l','--slice',
                action="callback",
                type="string",
                callback=get_slice_args,
                dest="slice_args",
                help="Slice page products from [start:end]. None is empty."),
        )

    def handle(self, url_slug, **options):
        page = Page.objects.get(url_slug=url_slug)
        PageMaintainer(page).update(options={
            'recreate_tiles': options['recreate_tiles'],
            'skip_images': not options['update_images'],
            'skip_tiles': True,
            'skip_similar_products': options['skip_similar_products'],
            'slice': options.get('slice_args', None),
            'project': 'pages' if options['scrape'] else 'datafeeds',
        })
        
