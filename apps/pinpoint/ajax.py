from django.core.files.images import get_image_dimensions
from django.conf import settings

def valid_dimensions( product_image ):
    """
    Ensures that the dimensions of the image are atleast the minimum dimensions
    for an image.  Returns true if valid, otherwise returns false.
    
    @return: bool
    """
    dimensions = get_image_dimensions( product_image )
    if  dimensions < (settings.MIN_MEDIA_WIDTH, settings.MIN_MEDIA_HEIGHT):
        # image has to be able to fit a wide block
        return False
    return True
