from django.contrib import admin

from apps.pinpoint.models import StoreTheme, BlockType, BlockContent, Campaign
from apps.assets.admin import BaseAdmin, BaseNamedAdmin


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
