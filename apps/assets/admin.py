from admin_extend.extend import extend_registered, add_bidirectional_m2m, registered_form
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db import models
from django.forms import SelectMultiple, ModelMultipleChoiceField


from .forms import CategoryForm, TagForm
from .models import BaseModel, Category, Store, Page, Tile, Feed, Product, \
                    ProductImage, Image, Content, Theme, Review, Video, Tag, Gif
from .utils import disable_tile_serialization


# Custom list display fields
def tile_count(obj):
    return obj.tiles.count()
tile_count.short_description = 'Tile Count'

def product_count(obj):
    return obj.product.count()
product_count.short_description = 'Product Count'

def tag_names(obj):
    tags = [tag.name for tag in obj.tags.all()]
    return ", ".join(tags)
tag_names.short_description = 'Tags'


class BaseAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'created_at',
        'updated_at'
    ]

    list_filter = []

    date_hierarchy = 'created_at'

    formfield_overrides = {
        models.ManyToManyField: {
            'widget': SelectMultiple(attrs={'size':'10'})
        },
    }

    search_fields = ('id', )


class BaseNamedAdmin(BaseAdmin):
    list_display = [
        'name',
        'description',
        'slug'
    ] + BaseAdmin.list_display

    search_fields = ['name']
    ordering = ['name']

    prepopulated_fields = {"slug": ("name",)}


class BaseNamedMediaAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display + ['remote', 'hosted', 'media_type']

    list_filter = BaseAdmin.list_filter + ['media_type']


class BaseNamedImageAdmin(BaseAdmin):
    list_display = ['id'] + BaseAdmin.list_display + ['remote', 'hosted']


class StoreAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['public_base_url']
    search_fields = ('id', 'name',)


class TagAdmin(BaseAdmin):
    list_display = ['name', 'id'] + BaseAdmin.list_display + ['store', 'url']
    filter_horizontal = ('products',)
    form = TagForm


class CategoryAdmin(BaseAdmin):
    list_display = ['name', 'id'] + BaseAdmin.list_display + ['store', 'url']
    filter_horizontal = ('tiles',)
    form = CategoryForm


class PageAdmin(BaseAdmin):
    list_display = ['name', 'url_slug'] + BaseAdmin.list_display
    search_fields = ('id', 'name', 'url_slug')


class TileAdmin(BaseAdmin):
    list_display = ['feed', 'template'] + BaseAdmin.list_display
    search_fields = ('id', 'template')
    list_filter = ('feed',)
    filter_horizontal = ('products', 'content',)

    def save_model(self, request, obj, form, change):
        """
        This method does not save m2m fields, they are split into a different call
        Skip full clean and tile serialization until saving m2m relations
        see: https://github.com/django/django/blob/stable/1.6.x/django/contrib/admin/options.py#L1263
        """
        if not change:
            with disable_tile_serialization():
                super(BaseModel, obj).save()
        else:
            obj.save()


class FeedAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display
    search_fields = ('id', 'page_id',)


class ProductAdmin(BaseAdmin):
    ordering = ['name']
    list_display = ['name', '_tag_names'] + BaseAdmin.list_display
    search_fields = ('id', 'name', 'description', 'sku',)
    exclude = ('default_image',)
    filter_horizontal = ('similar_products',)

    def _tags(self, obj):
        return [tag.name for tag in obj.tags.all()]

    def _tag_names(self, obj):
        return ", ".join(self._tags(obj))
    _tag_names.admin_order_field = 'tags'

class ProductImageAdmin(BaseAdmin):
    ordering = ['created_at', 'original_url']
    list_display = ['product', 'image_tag'] + BaseAdmin.list_display + ['original_url']
    search_fields = ('product__id', 'id',)


class ImageAdmin(BaseAdmin):
    ordering = ['created_at', 'original_url']
    search_fields = ('id', 'url', 'name', 'description')
    list_display = ['url'] + BaseAdmin.list_display + ['original_url']


class GifAdmin(BaseAdmin):
    ordering = ['created_at', 'original_url']
    search_fields = ('id', 'url', 'name', 'description', 'gif_url')
    list_display = ['gif_url'] + ['url'] + BaseAdmin.list_display + ['original_url']


class ContentAdmin(BaseAdmin):
    ordering = ['id']
    list_display = ['image_tag'] + BaseAdmin.list_display
    search_fields = ('id', 'url',)
    filter_horizontal = ('tagged_products',)
    readonly_fields = ('image_tag',)


class ThemeAdmin(BaseAdmin):
    list_display = ['name'] + BaseAdmin.list_display + ['store', 'template']
    search_fields = ('id', 'name', 'template',)


class ReviewAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display


class VideoAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display + ['url', 'source_url']
    search_fields = ('id', 'url', 'source_url',)


admin.site.register(Store, StoreAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(Tile, TileAdmin)
admin.site.register(Feed, FeedAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Gif, GifAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Content, ContentAdmin)
admin.site.register(Theme, ThemeAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Video, VideoAdmin)


@extend_registered
class ExtendedProductAdminForm(add_bidirectional_m2m(registered_form(Product))):

    tags = ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=FilteredSelectMultiple(verbose_name='tags', is_stacked=False),
        required=False,
    )

    def _get_bidirectional_m2m_fields(self):
        return super(ExtendedProductAdminForm, self).\
            _get_bidirectional_m2m_fields() + [('tags', 'tags')]
