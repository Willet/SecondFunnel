from django.contrib import admin

from apps.pinpoint.models import (StoreTheme, BlockType, Campaign,
                                  IntentRankCampaign)
from apps.assets.admin import BaseNamedAdmin


class StoreThemeAdmin(BaseNamedAdmin):
    pass

admin.site.register(StoreTheme, StoreThemeAdmin)


class BlockTypeAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['image', 'handler', 'enabled']

admin.site.register(BlockType, BlockTypeAdmin)


class IntentRankCampaignAdmin(BaseNamedAdmin):
    pass

admin.site.register(IntentRankCampaign, IntentRankCampaignAdmin)

class CampaignAdmin(BaseNamedAdmin):
    list_display = BaseNamedAdmin.list_display + ['live', 'store']
    list_filter = BaseNamedAdmin.list_filter + ['live']

admin.site.register(Campaign, CampaignAdmin)
