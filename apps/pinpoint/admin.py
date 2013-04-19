from django.contrib import admin

from apps.pinpoint.models import (StoreTheme, BlockType, BlockContent,
                        Campaign, StoreThemeMedia, FeaturedProductBlock, ShopTheLookBlock, IntentRankCampaign)
from apps.assets.admin import BaseAdmin, BaseNamedAdmin, BaseNamedMediaAdmin


class StoreThemeMediaAdmin(BaseNamedMediaAdmin):
    list_display = BaseNamedMediaAdmin.list_display + ['theme']
    list_filter = BaseNamedMediaAdmin.list_filter + ['theme']

admin.site.register(StoreThemeMedia, StoreThemeMediaAdmin)


class StoreThemeAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['store']
    list_filter = BaseNamedAdmin.list_filter + ['store']

admin.site.register(StoreTheme, StoreThemeAdmin)


class BlockTypeAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['image', 'handler', 'enabled']

admin.site.register(BlockType, BlockTypeAdmin)


class BlockContentAdmin(BaseAdmin):
    list_display = BaseAdmin.list_display + ['block_type', 'priority', 'data']
    list_filter = BaseAdmin.list_filter + ['block_type']

admin.site.register(BlockContent, BlockContentAdmin)

class IntentRankCampaignAdmin(BaseNamedAdmin):
    pass

admin.site.register(IntentRankCampaign, IntentRankCampaignAdmin)

class CampaignAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['live', 'store']
    list_filter = BaseNamedAdmin.list_filter + ['live']

admin.site.register(Campaign, CampaignAdmin)

class FeaturedProductBlockAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['product', 'get_image']
    list_filter = BaseNamedAdmin.list_filter + ['product']

admin.site.register(FeaturedProductBlock, FeaturedProductBlockAdmin)
admin.site.register(ShopTheLookBlock, FeaturedProductBlockAdmin)
