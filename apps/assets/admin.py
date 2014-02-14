from django.contrib import admin

from apps.assets.models import Store


class BaseAdmin(admin.ModelAdmin):
    list_display = [
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


class BaseNamedMediaAdmin(BaseNamedAdmin):
    list_display = ['id'] + BaseNamedAdmin.list_display + ['remote', 'hosted', 'media_type']

    list_filter = BaseNamedAdmin.list_filter + ['media_type']


class BaseNamedImageAdmin(BaseNamedAdmin):
    list_display = ['id'] + BaseNamedAdmin.list_display + ['remote', 'hosted']


class StoreAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display

admin.site.register(Store, StoreAdmin)
