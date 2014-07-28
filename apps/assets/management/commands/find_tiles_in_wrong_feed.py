from django.core.management.base import BaseCommand, CommandError
from apps.assets.models import Page

class Command(BaseCommand):
    args = ''
    help = 'Detects tiles that contain products/content from different stores.'

    def handle(self, *args, **options):
        self.verify_tiles()


    def verify_tiles(self):
        self.stdout.write('Checking...')
        for page in Page.objects.all():
            if not page.feed:
                continue

            for tile in page.feed.tiles.all():
                for product in tile.products.all():
                    if product.store.id != page.store.id:
                        print "{} is on the wrong page ({}) via {}".format(
                            product, page.id, tile)
                for content in tile.content.select_subclasses():
                    if content.store.id != page.store.id:
                        print "{} is on the wrong page ({}) via {}".format(
                            content, page.id, tile)
