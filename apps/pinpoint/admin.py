from django.contrib import admin

from apps.pinpoint.models import *

admin.site.register(UserProfile)
admin.site.register(MediaAsset)
admin.site.register(Product)
admin.site.register(Store)
admin.site.register(BlockType)
admin.site.register(BlockContent)
admin.site.register(Campaign)

