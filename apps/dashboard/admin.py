from django.contrib import admin

from apps.dashboard.models import DashBoard


class DashBoardAdmin(admin.ModelAdmin):  # dashboard site admin
    list_display = ('site', 'table_id')

admin.site.register(DashBoard, DashBoardAdmin)

