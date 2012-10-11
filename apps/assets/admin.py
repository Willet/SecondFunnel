from django.contrib import admin

from apps.assets.models import Product, Media, Store


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


class MediaAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['remote', 'hosted']

admin.site.register(Media, MediaAdmin)


class StoreAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['staff_count']

admin.site.register(Store, StoreAdmin)


class ProductAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['price', 'original_url']

admin.site.register(Product, ProductAdmin)
