from django.contrib import admin

from apps.pinpoint.models import *


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


class MediaAssetAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['remote', 'hosted']

admin.site.register(MediaAsset, MediaAssetAdmin)


class ProductAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['price', 'original_url']

admin.site.register(Product, ProductAdmin)


class StoreAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['staff_count']

admin.site.register(Store, StoreAdmin)


class StoreThemeAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['store']
    list_filter = ['store']

admin.site.register(StoreTheme, StoreThemeAdmin)


class BlockTypeAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['template_name']

admin.site.register(BlockType, BlockTypeAdmin)


class BlockContentAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display + ['block_type', 'priority', 'data']
    list_filter = ['block_type']

admin.site.register(BlockContent, BlockContentAdmin)


class CampaignAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['store']

admin.site.register(Campaign, CampaignAdmin)

admin.site.register(UserProfile)
