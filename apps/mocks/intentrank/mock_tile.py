# This is probably best put into a template, but I doubt we'll use it enough
# times to justify putting the time into it

from mock_image import get_image_url

DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 512

def mock_tile(id, host='localhost:8000'):
    image_url = get_image_url(width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, message=str(id))
    tile = {
        'default-image': id,
        'url': get_image_url(width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, message=str(id)),
        'tile-id': id,
        'format': 'png',
        'type': 'image',
        'template': 'product',
        'name': str(id),
        'description': str(id),
        'images': [
            {
                'id': id,
                'dominant-color': '#ffffff',
                'url': image_url,
                'sizes': {
                    'master': {
                        'width': DEFAULT_WIDTH,
                        'height': DEFAULT_HEIGHT
                    },
                    'grande': {
                        'width': DEFAULT_WIDTH,
                        'height': DEFAULT_HEIGHT
                    },
                    'large': {
                        'width': DEFAULT_WIDTH,
                        'height': DEFAULT_HEIGHT
                    }
                }
            }
        ]

    }

    return tile
