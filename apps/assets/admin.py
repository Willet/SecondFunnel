from django.contrib import admin

from apps.assets.models import Product, ProductMedia, Store


class BaseAdmin(admin.ModelAdmin):
    list_display = [
        'created',
        'last_modified'
    ]

    date_hierarchy = 'created'


class BaseNamedAdmin(BaseAdmin):
    list_display = [
        'name',
        'description',
        'slug'
    ] + BaseAdmin.list_display

    prepopulated_fields = {"slug": ("name",)}


class BaseNamedMediaAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['remote', 'hosted']


class ProductMediaAdmin(BaseNamedMediaAdmin):
    list_display = BaseNamedMediaAdmin.list_display + ['product']
    list_filter = ['product']

admin.site.register(ProductMedia, ProductMediaAdmin)


class StoreAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['staff_count']

admin.site.register(Store, StoreAdmin)


class ProductAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['price', 'original_url']

admin.site.register(Product, ProductAdmin)
