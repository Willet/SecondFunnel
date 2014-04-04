from django.contrib import admin
from django.db import models
from django.forms import SelectMultiple

from apps.assets.models import (Store, Page, Tile, Feed, Product, ProductImage,
                                Image, Content, Theme, Review, Video, TileRelation, Category)


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


class PageAdmin(BaseAdmin):
    list_display = ['name', 'url_slug'] + BaseAdmin.list_display
    search_fields = ('id', 'name', 'url_slug')


class TileAdmin(BaseAdmin):
    list_display = ['feed', 'template', 'prioritized',
                    'click_starting_score', 'click_score',
                    'view_starting_score', 'view_score'] + BaseAdmin.list_display
    search_fields = ('id', 'template')
    list_filter = ('feed',)
    filter_horizontal = ('products', 'content',)


class TileRelationAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display + ['tile_a_id', 'tile_b_id', 'starting_score', 'score']
    search_fields = ('id', 'tile_a_id', 'tile_b_id',)

    def tile_a_id(self, obj):
        return str(obj.tile_a.id)

    tile_a_id.short_description = 'tile_a_id'

    def tile_b_id(self, obj):
        return str(obj.tile_b.id)

    tile_b_id.short_description = 'tile_b_id'


class FeedAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display
    search_fields = ('id', 'page_id',)


class ProductAdmin(BaseAdmin):
    ordering = ['name']
    list_display = ['name', '_category_names'] + BaseAdmin.list_display
    list_filter = ('categories__name',)
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
admin.site.register(TileRelation, TileRelationAdmin)
admin.site.register(Feed, FeedAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Content, ContentAdmin)
admin.site.register(Theme, ThemeAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Video, VideoAdmin)
