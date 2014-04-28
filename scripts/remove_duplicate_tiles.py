#!/usr/bin/env python


def remove_duplicate_tiles(page):
    """Takes a page and removes all tiles that have duplicate
    products and content.
    """
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


if __name__ == '__main__':
    from apps.assets.models import Page
    for page in Page.objects.all():
        remove_duplicate_tiles(page)
