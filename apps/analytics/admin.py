from django.contrib import admin

from apps.analytics.models import (AnalyticsRecency, Category, Metric,
    KVStore, CategoryHasMetric, SharedStorage)


class AnalyticsRecencyAdmin(admin.ModelAdmin):
    list_display = [
        'parent', 'last_fetched']

admin.site.register(AnalyticsRecency, AnalyticsRecencyAdmin)


class AnalyticsBase(admin.ModelAdmin):
    list_display = ('name', 'enabled')
    list_filter = ('enabled',)
    prepopulated_fields = {"slug": ("name",)}


class CategoryHasMetricInline(admin.TabularInline):
    model = CategoryHasMetric


class CategoryAdmin(AnalyticsBase):
    list_display = AnalyticsBase.list_display + ('metrics_count',)
    inlines = [
        CategoryHasMetricInline,
    ]

admin.site.register(Category, CategoryAdmin)


class MetricAdmin(AnalyticsBase):
    list_display = AnalyticsBase.list_display + ('data_count',)

admin.site.register(Metric, MetricAdmin)


class KVStoreAdmin(admin.ModelAdmin):
    list_display = ('parent', 'target', 'key', 'value', 'meta', 'timestamp')
    list_filter = ('key',)

admin.site.register(KVStore, KVStoreAdmin)


class SharedStorageAdmin(admin.ModelAdmin):
    list_display = ('id',)

admin.site.register(SharedStorage, SharedStorageAdmin)
