

class ProcessingHooksMixin(object):
    """
    A Spider Mixin: hooks can be optionally overwritten in the spiders for individual clients

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