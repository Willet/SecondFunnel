from django.contrib import admin

from apps.analytics.models import AnalyticsData, AnalyticsRecency


class AnalyticsDataAdmin(admin.ModelAdmin):
    list_display = [
        'parent', 'date', 'key', 'value']

    save_as = True

admin.site.register(AnalyticsData, AnalyticsDataAdmin)


class AnalyticsRecencyAdmin(admin.ModelAdmin):
    list_display = [
        'parent', 'last_fetched']

admin.site.register(AnalyticsRecency, AnalyticsRecencyAdmin)
