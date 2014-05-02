from admin_extend.extend import extend_registered, add_bidirectional_m2m, registered_form
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db import models
from django.forms import SelectMultiple, ModelMultipleChoiceField

from apps.assets.forms import CategoryForm
from apps.assets.models import (Store, Page, Tile, Feed, Product, ProductImage,
                                Image, Content, Theme, Review, Video, Category)


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


class CategoryAdmin(BaseAdmin):
    list_display = ['name', 'id'] + BaseAdmin.list_display + ['store', 'url']
    filter_horizontal = ('products',)
    form = CategoryForm


class PageAdmin(BaseAdmin):
    list_display = ['name', 'url_slug'] + BaseAdmin.list_display
    search_fields = ('id', 'name', 'url_slug')


class TileAdmin(BaseAdmin):
    list_display = ['feed', 'template', 'prioritized'] + BaseAdmin.list_display
    search_fields = ('id', 'template')
    list_filter = ('feed',)
    filter_horizontal = ('products', 'content',)


class FeedAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display
    search_fields = ('id', 'page_id',)


class ProductAdmin(BaseAdmin):
    ordering = ['name']
    list_display = ['name', '_category_names'] + BaseAdmin.list_display
    #list_filter = ('categories__name',) #Commenting this line out made it so I could see the product page on my local
    search_fields = ('id', 'name', 'description', 'sku',)

    def _categories(self, obj):
        return [cat.name for cat in obj.categories.all()]

    def _category_names(self, obj):
        return ", ".join(self._categories(obj))
    _category_names.admin_order_field = 'categories'

class ProductImageAdmin(BaseAdmin):
    ordering = ['created_at', 'original_url']
    list_display = ['product', 'image_tag'] + BaseAdmin.list_display + ['original_url']
    search_fields = ('product__id', 'id',)


class ImageAdmin(BaseAdmin):
    ordering = ['created_at', 'original_url']
    list_display = ['url'] + BaseAdmin.list_display + ['original_url']


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
admin.site.register(Category, CategoryAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(Tile, TileAdmin)
admin.site.register(Feed, FeedAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Content, ContentAdmin)
admin.site.register(Theme, ThemeAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Video, VideoAdmin)


@extend_registered
class ExtendedProductAdminForm(add_bidirectional_m2m(registered_form(Product))):

    categories = ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=FilteredSelectMultiple(verbose_name='categories', is_stacked=False),
        required=False,
    )

    def _get_bidirectional_m2m_fields(self):
        return super(ExtendedProductAdminForm, self).\
            _get_bidirectional_m2m_fields() + [('categories', 'categories')]
