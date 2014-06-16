from django.contrib import admin

from apps.dashboard.models import DashBoard, UserProfile, AnalyticsQuery, ClickmeterQuery, Campaign

admin.site.register(DashBoard)
admin.site.register(UserProfile)
admin.site.register(AnalyticsQuery)
admin.site.register(ClickmeterQuery)
admin.site.register(Campaign)
