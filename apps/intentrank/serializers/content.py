from apps.utils.functional import find_where

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
            "currency": product.currency,
            "description": product.description,
            "details": product.details,
            "name": product.name,
            "tagged-products": [],
            "id": product.id,
            "in-stock": product.in_stock,
        }

        data.update(camelize_JSON(product.attributes))

        try:
            data["default-image"] = product.default_image.serializer().get_dump_object(product.default_image)
        except AttributeError:
            try:
                # fall back to first image
                data["default-image"] = product_images[0].serializer().get_dump_object(product_images[0])
            except (IndexError, AttributeError):
                data['default-image'] = {}
        
        if shallow:
            # Just have the default image & skip similar products
            data["images"] = [data["default-image"]] if data['default-image'] else []
        else:
            # Order images
            if product.attributes.get('product_images_order'):
                # If image ordering is explicitly given, use it
                ordered_images = []
                for i in product.attributes.get('product_images_order', []):
                    try:
                        ordered_images.append(find_where(product_images, i))
                    except ValueError:
                        pass  # could not find matching product image
                product_images = ordered_images
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

            data["images"] = [image.serializer().get_dump_object(image) for image in product_images]

            # Include a shallow similar_products. Prevents infinite loop
            similar_products = product.similar_products.filter(placeholder=False)
            if not product.store.display_out_of_stock:
                similar_products = similar_products.filter(in_stock=True)

            for product in similar_products:
                data['tagged-products'].append(self.get_dump_object(product, shallow=True))

        return data


class ProductImageSerializer(IRSerializer):
    """This dumps some fields from the image as JSON."""
    def get_dump_object(self, product_image):
        """This will be the data used to generate the object."""
        default_image_sizes = {
            'master': {
                'url': product_image.url,
                'width': product_image.width or '100%',
                'height': product_image.height or '100%',
            },
        }

        data = {
            "format": product_image.file_type or "jpg",
            "type": "image",
            "dominant-color": product_image.dominant_color or "transparent",
            "url": product_image.url,
            "id": product_image.id,
            "sizes": dict(product_image.image_sizes) or default_image_sizes,
            "orientation": product_image.orientation,
        }

        data.update(camelize_JSON(product_image.attributes))
        data['productShot'] = product_image.is_product_shot

        return data


class ContentSerializer(IRSerializer):
    def get_dump_object(self, content):
        data = {
            'id': content.id,
            'store-id': content.store.id,
            'source': content.source,
            'source_url': content.source_url,
            'url': content.url or content.source_url,
            'author': content.author,
            'status': content.status,
            'tagged-products': [],
        }
        data.update(camelize_JSON(content.attributes))

        tagged_products = content.tagged_products.filter(placeholder=False)
        if not content.store.display_out_of_stock:
            tagged_products = tagged_products.filter(in_stock=True)

        for product in tagged_products:
            data['tagged-products'].append(product.serializer().get_dump_object(product, shallow=True))

        return data


class ImageSerializer(ContentSerializer):
    """This dumps some fields from the image as JSON."""
    def get_dump_object(self, image):
        """This will be the data used to generate the object."""
        default_image_sizes = {
            'master': {
                'url': image.url,
                'width': image.width or '100%',
                'height': image.height or '100%',
            }
        }

        data = super(ImageSerializer, self).get_dump_object(image)
        data.update({
            "format": image.file_type or "jpg",
            "type": "image",
            "dominant-color": image.dominant_color or "transparent",
            "sizes": image.attributes.get('sizes', default_image_sizes),
            "orientation": image.orientation or "portrait",
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
        default_image_sizes = {
            'master': {
                'url': gif.url,
                'width': gif.width or '100%',
                'height': gif.height or '100%',
            }
        }

        data = super(GifSerializer, self).get_dump_object(gif)
        data.update({
            "format": gif.file_type or "gif",
            "type": "image",
            "dominant-color": gif.dominant_color or "transparent",
            "sizes": gif.attributes.get('sizes', default_image_sizes),
            "orientation": gif.orientation or "portrait",
            "gifUrl": gif.gif_url,
        })

        return data


class VideoSerializer(ContentSerializer):
    """This will dump absolutely everything in a product as JSON."""
    def get_dump_object(self, video):

        data = super(VideoSerializer, self).get_dump_object(video)

        data.update({
            "type": "video",
            "caption": video.caption or '',
            "description": video.description or '',
            "original-id": video.original_id or video.id,
            "original-url": video.source_url or video.url,
            "source": video.source or 'youtube',
        })

        return data

