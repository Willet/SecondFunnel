from django.core.management.base import BaseCommand
import traceback
from optparse import make_option

from apps.assets.models import Page
from apps.imageservice.models import SizeConf
from apps.imageservice.tasks import transfer_cloudinary_image_to_s3


class Command(BaseCommand):
    help = """Transfers the most common sizes of product tile cover images from
    Cloudinary to Cloudfront/S3 CDN. Updates ProductImage models with S3 image locations.

    Usage:
    python manage.py transfer_page_images [-n, --num-tiles: <Number>] <url_slug>

    url_slug
        Url slug of the page to transfer images 

    -n, --num-tiles
        Number of tiles to transfer, starting with the highest priority.
        Naive implementation, assumes the tiles are prioritized.
    """
    option_list = BaseCommand.option_list + (
            make_option('-n','--num-tiles',
                type="int",
                dest="num_tiles",
                default=200,
                help="Transfer this many tiles starting from the highest priority."),
        )

    def handle(self, url_slug, **options):
        page = Page.objects.get(url_slug=url_slug)
        store = page.store
        sizes = []

        # theme.image_sizes format: 'tile': { 'width': 700, 'height': 700 }
        # One of width or height can be None, but not both
        # Size names are not significant & only used for folder names BUT they must be unique
        for name, size in page.theme.image_sizes.items():
            sizes.append(
                SizeConf(name=name, 
                         width=size.get('width', None),
                         height=size.get('height', None)
                )
            )

        num_tiles = options.get('num_tiles', 200) # Default is 200 tiles
        tiles = page.feed.tiles.order_by("-priority")[0:num_tiles]
        print "Will attempt to transfer {} tile images for {}".format(tiles.count(), url_slug)

        for t in tiles.iterator():
            cover_image = None

            #  get the cloudinary image to transfer
            if t.template == "product" and not t.placeholder:
                cover_image = t.products.first().default_image
            
            # Add hooks for more template types here

            if t.placeholder:
                print "Skipping '{}' {} because it is a placeholder".format(t.template, t)
            elif not cover_image:
                print "Skipping '{}' {} because template type is not configured".format(t.template, t)
            elif not hasattr(cover_image, 'url'):
                print "Skipping '{}' {} because it has no default image".format(t.template, t)
            elif not "cloudinary.com" in cover_image.url:
                print "Skipping '{}' {} because default image is not a cloudinary image.".format(t.template, t)
            else:
                # Ex: http://res.cloudinary.com/secondfunnel/image/upload
                #            /v1441808107/sur%20la%20table/6a6bd03ec8a5b8ce.jpg
                for size in sizes:
                    try:
                        (s3_image, s3_url) = transfer_cloudinary_image_to_s3(cover_image.url, store, size)
                    except:
                        traceback.print_exc()
                        continue
                    else:
                        # update product image with size / url combo
                        if not cover_image.attributes['sizes']:
                            cover_image.attributes['sizes'] = {}
                        cover_image.attributes['sizes'][size.name] = {
                            'width': s3_image.width,
                            'height': s3_image.height,
                            'url': s3_url,
                        }
                    cover_image.save(update_fields=['attributes'])
                print "{} moved to s3.".format(cover_image)


