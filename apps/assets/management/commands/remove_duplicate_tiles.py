from django.core.management.base import BaseCommand, CommandError
from apps.assets.models import Page

class Command(BaseCommand):
    args = '<page_id page_id ...>'
    help = 'Takes a page or list of pages and removes all tiles that have duplicate products and content. If no page is provided runs on all pages.'

    def handle(self, *args, **options):
        if len(args) == 0:
            for page in Page.objects.all():
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
        tiles = page.feed.get_tiles()
        tiles_dict = {}

        for tile in tiles:
            key = 'p:%s c:%s' % (
                ','.join(map(lambda x: str(x['id']), tile.products.all().order_by('id').values('id'))),
                ','.join(map(lambda x: str(x['id']), tile.content.all().order_by('id').values('id'))),
            )

            if key in tiles_dict:
                tile.delete()
            else:
                tiles_dict[key] = True
