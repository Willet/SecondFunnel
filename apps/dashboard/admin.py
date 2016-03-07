from django.contrib import admin

from apps.dashboard.models import Dashboard, UserProfile, AnalyticsQuery, ClickmeterQuery, Campaign, KeenIOMetricsQuery

admin.site.register(Dashboard)
admin.site.register(UserProfile)
admin.site.register(AnalyticsQuery)
admin.site.register(ClickmeterQuery)
admin.site.register(Campaign)
admin.site.register(KeenIOMetricsQuery)
