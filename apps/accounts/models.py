from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('support', 'Support'),
        ('viewer', 'Viewer'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    last_active = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    whatsapp_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_users'
    )

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.role})"

    def save(self, *args, **kwargs):
        # Auto-assign to Django Group based on role
        super().save(*args, **kwargs)
        if self.role:
            group, _ = Group.objects.get_or_create(name=self.role.capitalize())
            self.groups.set([group])


class UserActivityLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('device_block', 'Device Blocked'),
        ('device_unblock', 'Device Unblocked'),
        ('router_restart', 'Router Restarted'),
        ('settings_change', 'Settings Changed'),
        ('subscription_created', 'Subscription Created'),
        ('subscription_deleted', 'Subscription Deleted'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']