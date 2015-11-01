from apps.scrapy.items import ScraperProduct, ScraperImage


class ProcessingMixin(object):
    """
    A Spider Mixin: hooks and methods to make spiders more useful in scraping
    """
    """
    Pipeline item preparation methods, to be called within a spider
    """
    @staticmethod
    def handle_product_tagging(response, item, product_id=None, content_id=None):
        """
        Call this on product or content items to handle tagging. If `product_id`
        or `content_id` are provided AND this item is not already tagged for another
        item, then it is caught by the AssociateWithProductsPipeline for tagging.

        Subsequent product requests that should be tagged to this item MUST
        run through `prep_product_tagging`

        @param response: scrapy <Response>
        @param item: <ScraperProduct> or <ScraperImage>
        @param product_id: (optional) <str> or <int> - an id to tag 
        @param content_id: (optional) <str> or <int> - an id to tag 

        Note: this method should be called after item is loaded but before yield'ing
        """
        if item isinstance ScraperProduct:
            # Handle tagged products for content
            if response.meta.get('content_id_to_tag', False):
                item['force_skip_tiles'] = True
                item['content_id_to_tag'] = response.meta.get('content_id_to_tag', False)

            # Handle similar products for a product
            elif response.meta.get('product_id_to_tag', False):
                item['force_skip_tiles'] = True
                item['product_id_to_tag'] = response.meta.get('product_id_to_tag', False)

            elif product_id:
                # Not a similar product, prep for tagging
                item['tag_with_products'] = True # Command to AssociateWithProductsPipeline
                item['product_id'] = product_id

        if item isinstance ScraperImage:
            if content_id:
                item['tag_with_products'] = True # Command to AssociateWithProductsPipeline
                item['content_id'] = content_id

    @staticmethod
    def prep_product_tagging(request, item):
        """
        Call this after loading an item on subsequent product requests that will be tagged
        to the original item (content or product)

        @param request scrapy <Request>
        @param item <ScraperProduct> or <ScraperImage>
        """
        if item.get('content_id', False):
            request.meta['content_id_to_tag'] = item['content_id']
        elif item.get('product_id', False)
            request.meta['product_id_to_tag'] = item['product_id']

    """
    The hooks can be optionally overwritten in the spiders for individual clients

    Various parts of the scrapy app call these hooks (controller, pipelines, etc)
    """
    @staticmethod
    def clean_url(url):
        """Hook for cleaning url before scraping
        Returns: cleaned url 

        See controller.py """
        return url

    @staticmethod
    def choose_default_image(product):
        """ Returns: image to set as default image, must be one of product_images 

        See pipelines.py """
        return product.product_images.first()

    @staticmethod
    def on_product_finished(product):
        """Hook for post-processing a product after scrapy is finished with it

        See pipelines.py """
        pass

    @staticmethod
    def on_image_finished(image):
        """Hook for post-processing a product after scrapy is finished with it

        See pipelines.py """
        pass

    @staticmethod
    def on_tile_finished(tile, obj):
        """ Hook for post-processing a tile after scrapy is finished with it
        Only called if spider is creating tiles

        tile - Tile instance
        obj - Product or Image instance that was scraped - useful if Tile is tagged >1 things 

        See pipelines.py """
        pass
