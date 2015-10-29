

class ProcessingMixin(object):
    """
    A Spider Mixin: hooks and methods to make spiders more useful in scraping
    """
    """
    Pipeline item preparation methods, to be called within a spider
    """
    @staticmethod
    def handle_product_tagging(response, item, product_id=None):
        """
        If this product is to be tagged to content or product, skip turning it into a tile

        Else if this spider provides a product_id, then prep for this to be tagged

        Note: a) should only be called on products
              b) this method should be called after item is loaded but before yield'ing
        """
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
