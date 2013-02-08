from django.contrib import admin
from django.utils.safestring import mark_safe

from apps.assets.models import Product, ProductMedia, Store, GenericMedia, GenericImage, YoutubeVideo, ExternalContentType, ExternalContent


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

    search_fields = ['name']

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
        'store', 'original_url', 'price', 'media_count', 'lifestyleImage']

    list_filter = BaseNamedAdmin.list_filter + ['store',]

    inlines = [
        ProductMediaInline,
    ]

    readonly_fields = ('lifestyle_preview', )

    def lifestyle_preview(self, obj):
        try:
            url = obj.lifestyleImage.get_url()
            return mark_safe("<img src='{url}' />".format(url=url))
        except AttributeError:
            return "No Image Available"


admin.site.register(Product, ProductAdmin)


class YoutubeVideoAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display + [
        'video_id', 'store']

admin.site.register(YoutubeVideo, YoutubeVideoAdmin)

class ExternalContentTypeAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['enabled']

admin.site.register(ExternalContentType, ExternalContentTypeAdmin)

class ExternalContentAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display + ['original_id',
                                                  'original_url',
                                                  'content_type',
                                                  'text_content']

admin.site.register(ExternalContent, ExternalContentAdmin)