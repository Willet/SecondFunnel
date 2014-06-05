from django.contrib import admin

from apps.dashboard.models import DashBoard, UserProfile


class DashBoardAdmin(admin.ModelAdmin):  # dashboard site admin
    list_display = ('site_name', 'table_id')

admin.site.register(DashBoard, DashBoardAdmin)
admin.site.register(UserProfile)

