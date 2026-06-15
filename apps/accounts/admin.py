from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserActivityLog, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'is_online', 'last_active', 'phone_number']
    list_filter = ['role', 'is_active', 'is_online', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('WiFi Manager Profile', {
            'fields': ('role', 'phone_number', 'avatar', 'timezone', 'two_factor_enabled',
                       'whatsapp_notifications', 'email_notifications', 'created_by')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role', {
            'fields': ('role', 'phone_number'),
        }),
    )


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__username', 'details']


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'expires_at', 'used', 'created_at']
    list_filter = ['used', 'created_at']