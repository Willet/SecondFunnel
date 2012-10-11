from django.contrib import admin

from apps.pinpoint.models import StoreTheme, BlockType, BlockContent, Campaign, StoreThemeMedia
from apps.assets.admin import BaseAdmin, BaseNamedAdmin, BaseNamedMediaAdmin


class StoreThemeMediaAdmin(BaseNamedMediaAdmin):
    list_display = BaseNamedMediaAdmin.list_display + ['theme']
    list_filter = ['theme']

admin.site.register(StoreThemeMedia, StoreThemeMediaAdmin)


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
