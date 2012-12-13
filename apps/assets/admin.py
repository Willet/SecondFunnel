from django.contrib import admin

from apps.assets.models import Product, ProductMedia, Store, GenericMedia, GenericImage, YoutubeVideo


class BaseAdmin(admin.ModelAdmin):
    list_display = [
        'created',
        'last_modified'
    ]

    list_filter = []

    date_hierarchy = 'created'


class BaseNamedAdmin(BaseAdmin):
    list_display = [
        'name',
        'description',
        'slug'
    ] + BaseAdmin.list_display

    prepopulated_fields = {"slug": ("name",)}


class BaseNamedMediaAdmin(BaseNamedAdmin):
    list_display = ['id'] + BaseNamedAdmin.list_display + [
        'remote', 'hosted', 'media_type']

    list_filter = BaseNamedAdmin.list_filter + ['media_type']


class BaseNamedImageAdmin(BaseNamedAdmin):
    list_display = ['id'] + BaseNamedAdmin.list_display + [
        'remote', 'hosted']


class GenericMediaAdmin(BaseNamedMediaAdmin):
    pass

admin.site.register(GenericMedia, GenericMediaAdmin)


class GenericImageAdmin(BaseNamedImageAdmin):
    pass

admin.site.register(GenericImage, GenericImageAdmin)


class ProductMediaAdmin(BaseNamedImageAdmin):
    list_display = BaseNamedImageAdmin.list_display + ['product']
    list_filter = BaseNamedImageAdmin.list_filter + ['product']

admin.site.register(ProductMedia, ProductMediaAdmin)


class StoreAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['staff_count']

admin.site.register(Store, StoreAdmin)


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia


class ProductAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + [
        'original_url', 'price', 'media_count', 'lifestyleImage']

    inlines = [
        ProductMediaInline,
    ]

admin.site.register(Product, ProductAdmin)


class YoutubeVideoAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display + [
        'video_id', 'store']

admin.site.register(YoutubeVideo, YoutubeVideoAdmin)
