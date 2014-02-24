from django.contrib import admin

from apps.assets.models import Store, Page, Tile, Feed


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
    list_display = ['id'] + BaseAdmin.list_display + ['remote', 'hosted', 'media_type']

    list_filter = BaseAdmin.list_filter + ['media_type']


class BaseNamedImageAdmin(BaseAdmin):
    list_display = ['id'] + BaseAdmin.list_display + ['remote', 'hosted']


class StoreAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display


class PageAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display


class TileAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display


class FeedAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display


admin.site.register(Store, StoreAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(Tile, TileAdmin)
admin.site.register(Feed, FeedAdmin)
