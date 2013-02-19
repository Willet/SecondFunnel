import random
from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import striptags
from django.utils.html import escape


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        abstract = True


class BaseModelNamed(BaseModel):
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    slug = models.SlugField(blank=True, null=True)

    class Meta:
        abstract = True


class Store(BaseModelNamed):
    staff = models.ManyToManyField(User)

    def __unicode__(self):
        return self.name

    def staff_count(self):
        return self.staff.all().count()


class MediaBase(BaseModelNamed):
    MEDIA_TYPES = (
        ('js', 'JavaScript'),
        ('css', 'CSS'),
        ('img', 'Image'),
    )
    remote = models.CharField(
        "Remote URL",
        max_length=555, blank=True, null=True)

    hosted = models.FileField(
        "Hosted File",
        upload_to="product_images",
        blank=True,
        null=True)

    media_type = models.CharField(
        max_length=3,
        choices=MEDIA_TYPES,
        default="css",
        blank=True,
        null=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return u"Media Asset URL %s" % self.get_url()

    def get_url(self):
        if self.remote:
            return self.remote

        if self.hosted:
            return self.hosted.url

        return None


class ImageBase(BaseModelNamed):
    remote = models.CharField(
        "Remote URL",
        max_length=555,
        blank=True,
        null=True)

    hosted = models.ImageField(
        "Hosted File",
        upload_to="product_images",
        blank=True,
        null=True)

    class Meta:
        abstract = True

    def get_url(self):
        if self.remote:
            return self.remote

        if self.hosted:
            return self.hosted.url

        return None

    def __unicode__(self):
        return self.get_url()


class GenericMedia(MediaBase):
    pass


class GenericImage(ImageBase):
    pass


class Product(BaseModelNamed):
    original_url = models.CharField(max_length=500, blank=True, null=True)

    store = models.ForeignKey(Store, blank=True, null=True)

    price = models.CharField(max_length=255, blank=True, null=True)
    sku = models.CharField(max_length=255, blank=True, null=True)

    last_scraped = models.DateTimeField(blank=True, null=True)
    rescrape = models.BooleanField(default=False)

    lifestyleImages = models.ManyToManyField(GenericImage, blank=True, null=True,
                                       related_name='associated_products')

    default_image = models.ForeignKey("ProductMedia", blank=True, null=True,
                                      related_name='primary_product')

    available = models.BooleanField(default=True)

    def __unicode__(self):
        return unicode(self.name) or u''

    def media_count(self):
        return self.media.count()

    # Template Aliases
    def url(self):
        return self.original_url

    def images(self):
        return [x.get_url() for x in self.media.all()]

    def data(self, raw=False):
        """HTML string representation of some of the product's properties.

        If raw, then the return value remains a dict.
        """
        def strip_and_escape(text):
            modified_text = striptags(text)
            modified_text = escape(modified_text)
            return modified_text

        external_content = []
        images = self.images()

        if self.default_image:
            image = self.default_image.get_url()
            images.insert(0, image)
        else:
            image = images[0] if images else None

        # add instagram images to image list
        for content in self.external_content.all():
            external_content.append({
                'original-id': content.original_id,
                'original-url': content.original_url,
                'content-type': content.content_type.name,
                'image-url': content.image_url,
            })

            if content.content_type.name.lower() == 'instagram':
                images.append(content.image_url)

        fields = {
            'data-title': strip_and_escape(self.name),
            'data-description': strip_and_escape(self.description),
            'data-price': strip_and_escape(self.price),
            'data-url': strip_and_escape(self.original_url),
            'data-image': strip_and_escape(image),
            'data-images': '|'.join(strip_and_escape(x) for x in images),
            'data-external-content': '|'.join(strip_and_escape(x.get('image-url', '')) for x in external_content),
            'data-product-id': self.id,
        }

        if self.lifestyleImages.all():
            # TODO: Do we want to select lifestyle images differently?
            random_idx = random.randint(0, self.lifestyleImages.count()-1)
            random_img = self.lifestyleImages.all()[random_idx]
            fields['data-lifestyle_image'] = strip_and_escape(random_img)

        if raw:
            data = {}
            for field in fields:
                # strip 'data-'
                field_name = field[5:]
                if field_name == 'images':
                    data[field_name] = filter(None, fields[field].split('|'))
                elif field_name == 'external-content':
                    data[field_name] = external_content
                else:
                    data[field_name] = fields[field]
        else:
            data = ''
            for field in fields:
                data = data + " %s='%s'" % (field, fields[field])

        return data


class ProductMedia(ImageBase):
    product = models.ForeignKey(Product, related_name="media")


class YoutubeVideo(BaseModel):
    video_id = models.CharField(max_length=11)
    store = models.ForeignKey(Store, null=True, related_name="videos")


class ExternalContent(BaseModel):
    # "yes, 555 is arbitrary" - other developers
    original_id = models.CharField(max_length=555, blank=True, null=True)
    original_url = models.CharField(max_length=555, blank=True, null=True)
    content_type = models.ForeignKey("ExternalContentType")
    tagged_products = models.ManyToManyField(Product, blank=True, null=True,
                                             related_name='external_content')

    text_content = models.TextField(blank=True, null=True)
    image_url = models.CharField(max_length=555, blank=True, null=True)

    def __unicode__(self):
        return u''

# If we need different behaviour per model, just use a proxy model.

class ExternalContentType(BaseModelNamed):
    """i.e. "Instagram"."""
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return unicode(self.name) or u''
