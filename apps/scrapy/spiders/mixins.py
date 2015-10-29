

class ProcessingMixin(object):
    """
    A Spider Mixin: hooks and methods to make spiders more useful in scraping
    """
    """
    Pipeline control methods
    """
    def if_similar_product(self, loader, *args):
        """
        If one of args has an id, self is a similar product. Let AssociateWithProductsPipeline
        handle it
        """
        for arg in args if arg:
            l.add_value('force_skip_tiles', True)
            loader.add_value('product_id_to_tag', arg)
            return

    def if_tagged_product(self, loader, *args):
        """
        If one of args has an id, self is a tagged product. Let AssociateWithProductsPipeline
        handle it
        """
        for arg in args if arg:
            l.add_value('force_skip_tiles', True)
            loader.add_value('content_id_to_tag', arg)
            return

    """
    hooks can be optionally overwritten in the spiders for individual clients

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
