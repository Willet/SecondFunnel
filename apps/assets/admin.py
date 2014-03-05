from django.contrib import admin

from apps.assets.models import (Store, Page, Tile, Feed, Product, ProductImage,
                                Image, Content, Theme, Review, Video)


class BaseAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'created_at',
        'updated_at'
    ]

    list_filter = []

    date_hierarchy = 'created_at'


class BaseNamedAdmin(BaseAdmin):
    list_display = [
        'name',
        'description',
        'slug'
    ] + BaseAdmin.list_display

    search_fields = ['name']

    prepopulated_fields = {"slug": ("name",)}


class BaseNamedMediaAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display + ['remote', 'hosted', 'media_type']

    list_filter = BaseAdmin.list_filter + ['media_type']


class BaseNamedImageAdmin(BaseAdmin):
    list_display = ['id'] + BaseAdmin.list_display + ['remote', 'hosted']


class StoreAdmin(BaseNamedAdmin):
    list_display = ['old_id'] + BaseNamedAdmin.list_display + ['public_base_url']


class PageAdmin(BaseAdmin):
    list_display = ['old_id'] + BaseAdmin.list_display


class TileAdmin(BaseAdmin):
    list_display = ['old_id'] + BaseAdmin.list_display + ['template', 'starting_score']


class FeedAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display


class ProductAdmin(BaseAdmin):
    list_display = ['old_id'] + BaseAdmin.list_display


class ProductImageAdmin(BaseAdmin):
    list_display = ['old_id'] + BaseAdmin.list_display + ['url', 'original_url']


class ImageAdmin(BaseAdmin):
    list_display = ['old_id'] + BaseAdmin.list_display + ['url', 'original_url']


class ContentAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display


class ThemeAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display + ['store', 'template']


class ReviewAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display


class VideoAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display + ['url', 'source_url']


admin.site.register(Store, StoreAdmin)
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
