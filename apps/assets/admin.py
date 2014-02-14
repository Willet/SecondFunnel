from django.contrib import admin

from apps.assets.models import Product, Store


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


class StoreAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['staff_count']

admin.site.register(Store, StoreAdmin)


class ProductAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + [
        'store', 'original_url', 'price', 'available', ]

    list_filter = BaseNamedAdmin.list_filter + ['available', 'store',]
    list_editable = ['available',]

    search_fields = BaseNamedAdmin.search_fields + ['original_url']


admin.site.register(Product, ProductAdmin)
