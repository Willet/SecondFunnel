from django.contrib import admin
from django.utils.safestring import mark_safe

from apps.assets.models import Product, ProductMedia, Store, GenericMedia, \
    GenericImage, ExternalContentType, ExternalContent, StoreFeature


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


class StoreFeaturesAdmin(BaseNamedAdmin):
    pass

admin.site.register(StoreFeature, StoreFeaturesAdmin)


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia


class ProductAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + [
        'store', 'original_url', 'price', 'available', 'media_count',]

    list_filter = BaseNamedAdmin.list_filter + ['available', 'store',]
    list_editable = ['available',]

    filter_horizontal = ('lifestyleImages',)

    search_fields = BaseNamedAdmin.search_fields + ['original_url']

    inlines = [
        ProductMediaInline,
    ]

    readonly_fields = ('lifestyle_preview', )

    def lifestyle_preview(self, obj):
        try:
            html = []
            for image in obj.lifestyleImages.all():
                url  = image.get_url()
                html.append("<img src='{url}' /><br/>".format(url=url))
            return mark_safe(''.join(html))
        except AttributeError:
            return "No Image Available"


admin.site.register(Product, ProductAdmin)


class ExternalContentTypeAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['enabled']

admin.site.register(ExternalContentType, ExternalContentTypeAdmin)


class ExternalContentAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display + ['store', 'original_id',
                                                  'original_url',
                                                  'content_type',
                                                  'text_content']
    list_filter = BaseNamedAdmin.list_filter + ['store', 'categories']

    filter_horizontal = ('tagged_products',)
    
    class Media:
        js = ( "js/youtube_admin_look.js", )

    readonly_fields = ('preview', )

    def preview(self, obj):
        try:
            if 'youtube' in obj.original_url:
                id = obj.original_id
                return mark_safe('<iframe src="http://www.youtube.com/embed/' + id + '" width="720" height="480"> </iframe><br/>')
            else:
                url = obj.image_url
                return mark_safe("<img src='{url}' />".format(url=url))
        except AttributeError as e:
            return "Preview Unavailable"

admin.site.register(ExternalContent, ExternalContentAdmin)
