from django.contrib import admin

from apps.static_pages.models import StaticLog

class StaticLogAdmin(admin.ModelAdmin):
    list_display = ['parent', 'key', 'timestamp']

admin.site.register(StaticLog, StaticLogAdmin)
