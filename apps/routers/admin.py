from django.contrib import admin
from .models import Router

@admin.register(Router)
class RouterAdmin(admin.ModelAdmin):
    list_display = ['name', 'ip_address', 'status', 'router_type', 'bandwidth_limit', 'is_active_setup']
    list_filter = ['status', 'router_type', 'access_mode']
    search_fields = ['name', 'ip_address', 'mac_address']