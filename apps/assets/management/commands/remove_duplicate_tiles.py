from django.core.management.base import BaseCommand, CommandError
from apps.assets.models import Page


class Command(BaseCommand):
    args = '<page_id page_id ...>'
    help = 'Takes a page or list of pages and removes all tiles that have duplicate products and content. If no page is provided runs on all pages.'

    def handle(self, *args, **options):
        if len(args) == 0:
            for page in Page.objects.order_by('id'):
                self.remove_duplicate_tiles(page)
        else:
            for page_id in args:
                try:
                    page = Page.objects.get(id=int(page_id))
                except Page.DoesNotExist:
                    raise CommandError('Page with id: %s does not exist' % page_id)

                self.remove_duplicate_tiles(page)


    def remove_duplicate_tiles(self, page):
        self.stdout.write('Removing duplicates for page with id: %s' % page.id)
        tiles = page.feed.tiles.all()
        tiles_dict = {}

        for tile in tiles:
            key = 'p:%s c:%s' % (
                ','.join(str(x['id']) for x in tile.products.order_by('id').values('id')),
                ','.join(str(x['id']) for x in tile.content.order_by('id').values('id')),
            )

            if key in tiles_dict:
                tile.delete()
            else:
                tiles_dict[key] = True
