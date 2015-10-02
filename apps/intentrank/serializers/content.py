from apps.utils.functional import find_where, get_image_file_type

from .utils import IRSerializer, SerializerError, camelize_JSON


""" Serializers for models that make up tiles """


class ProductSerializer(IRSerializer):
    """This will dump absolutely everything in a product as JSON."""
    def get_dump_object(self, product, shallow=False):
        """This will be the data used to generate the object.
        These are core attributes that every tile has.
        """
        product_images = list(product.product_images.all())

        data = {
            "url": product.url,
            # products don't *always* have skus
            # -- nor are they unique
            # -- nor are they necessarily numbers
            "sku": getattr(product, "sku", ""),
            "price": product.price,
            "salePrice": product.sale_price,
            "description": product.description,
            "details": product.details,
            "name": product.name,
            "tagged-products": [],
            "id": product.id,
            "in-stock": product.in_stock,
        }

        data.update(camelize_JSON(product.attributes))

        try:
            data["default-image"] = product.default_image.to_json()
            data["sizes"] = product.default_image.get('sizes', None)
            data["orientation"] = product.default_image.orientation
        except AttributeError:
            try:
                # fall back to first image
                data["default-image"] = product_images[0].to_json()
                data["sizes"] = product_images[0].get('sizes', None)
                data["orientation"] = product_images[0].orientation
            except (IndexError, AttributeError):
                data['default-image'] = {}
                data['sizes'] = {}
                data['orientation'] = "portrait"

        
        if shallow:
            # Just have the default image & skip similar products
            data["images"] = [data["default-image"]]
        else:
            # Order images
            if product.attributes.get('product_images_order'):
                # If image ordering is explicitly given, use it
                for i in product.attributes.get('product_images_order', []):
                    try:
                        product_images.append(find_where(product_images, i))
                    except ValueError:
                        pass  # could not find matching product image
            elif product.default_image:
                # If default image is in product_images, move it to front
                try:
                    idx = product_images.index(product.default_image)
                except ValueError:  # default image not in list
                    pass  # bail ordering
                else:
                    product_images = [product.default_image] + \
                                     product_images[:idx] + \
                                     product_images[idx+1:]

            data["images"] = [image.to_json() for image in product_images]

            # Include a shallow similar_products. Prevents infinite loop
            for product in product.similar_products.filter(in_stock=True):
                data['tagged-products'].append(self.get_dump_object(product, shallow=True))

        return data


class ProductImageSerializer(IRSerializer):
    """This dumps some fields from the image as JSON."""
    def get_dump_object(self, product_image):
        """This will be the data used to generate the object."""

        data = {
            "format": product_image.file_type or "jpg",
            "type": "image",
            "dominant-color": product_image.dominant_color or "transparent",
            "url": product_image.url,
            "id": product_image.id,
            "sizes": product_image.attributes.get('sizes', {
                'width': getattr(product_image, "width", '100%'),
                'height': getattr(product_image, "height", '100%'),
            }),
            "orientation": product_image.orientation,
        }

        data.update(camelize_JSON(product_image.attributes))

        return data


class ContentSerializer(IRSerializer):
    def get_dump_object(self, content):
        data = {
            'id': str(content.id),
            'store-id': str(content.store.id if content.store else 0),
            'source': content.source,
            'source_url': content.source_url,
            'url': content.url or content.source_url,
            'author': content.author,
            'status': content.status,
        }

        data['tagged-products'] = []
        for product in content.tagged_products.filter(in_stock=True):
            data['tagged-products'].append(product.to_json())

        return data


class ImageSerializer(ContentSerializer):
    """This dumps some fields from the image as JSON."""
    def get_dump_object(self, image):
        """This will be the data used to generate the object."""
        from apps.assets.models import default_master_size

        ext = get_image_file_type(image.url)

        data = super(ImageSerializer, self).get_dump_object(image)
        data.update({
            "format": ext or "jpg",
            "type": "image",
            "dominant-color": getattr(image, "dominant_color", "transparent"),
            "status": image.status,
            "sizes": image.attributes.get('sizes', {
                'width': getattr(image, "width", '100%'),
                'height': getattr(image, "height", '100%'),
            }),
            "orientation": getattr(image, 'orientation', 'portrait'),
        })
        if getattr(image, 'description', False):
            data.update({"description": image.description})
        if getattr(image, 'name', False):
            data.update({"name": image.name})

        return data


class GifSerializer(ContentSerializer):
    """This dumps some fields from the image as JSON."""
    def get_dump_object(self, gif):
        """This will be the data used to generate the object."""
        from apps.assets.models import default_master_size

        ext = get_image_file_type(gif.url)

        data = super(GifSerializer, self).get_dump_object(gif)
        data.update({
            "format": ext or "gif",
            "type": "gif",
            "dominant-color": getattr(gif, "dominant_color", "transparent"),
            "status": gif.status,
            "sizes": gif.attributes.get('sizes', {
                'width': getattr(gif, "width", '100%'),
                'height': getattr(gif, "height", '100%'),
            }),
            "orientation": getattr(gif, "orientation", "portrait"),
            "gifUrl": gif.gif_url
        })

        return data


class VideoSerializer(ContentSerializer):
    """This will dump absolutely everything in a product as JSON."""
    def get_dump_object(self, video):

        data = super(VideoSerializer, self).get_dump_object(video)

        data.update({
            "type": "video",
            "caption": getattr(video, 'caption', ''),
            "description": getattr(video, 'description', ''),
            "original-id": video.original_id or video.id,
            "original-url": video.source_url or video.url,
            "source": getattr(video, 'source', 'youtube'),
        })

        if hasattr(video, 'attributes'):
            if video.attributes.get('username'):
                data['username'] = video.attributes.get('username')

        return data

