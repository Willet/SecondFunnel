from django.contrib import admin

from apps.analytics.models import AnalyticsRecency, Category, Metric, KVStore


class AnalyticsRecencyAdmin(admin.ModelAdmin):
    list_display = [
        'parent', 'last_fetched']

admin.site.register(AnalyticsRecency, AnalyticsRecencyAdmin)


class AnalyticsBase(admin.ModelAdmin):
    list_display = ('name', 'enabled')
    list_filter = ('enabled',)


class CategoryAdmin(AnalyticsBase):
    list_display = AnalyticsBase.list_display + ('metrics_count',)

admin.site.register(Category, CategoryAdmin)


class MetricAdmin(AnalyticsBase):
    list_display = AnalyticsBase.list_display + ('slug', 'data_count')
    prepopulated_fields = {"slug": ("name",)}

admin.site.register(Metric, MetricAdmin)


class KVStoreAdmin(admin.ModelAdmin):
    list_display = ('parent', 'key', 'value', 'timestamp')

admin.site.register(KVStore, KVStoreAdmin)
