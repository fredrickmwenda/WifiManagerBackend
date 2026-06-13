from django.db import models
from django.utils import timezone

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50)
    price_ksh = models.PositiveIntegerField(verbose_name='Price (KSH)')
    duration_hours = models.PositiveIntegerField(verbose_name='Duration (hours)')
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#00d4aa')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['price_ksh']

    def __str__(self):
        return f"{self.name} (KSH {self.price_ksh})"


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('expiring_soon', 'Expiring Soon'),
    ]

    device = models.ForeignKey('devices.Device', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscriptions')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.end_time:
            self.end_time = timezone.now() + timezone.timedelta(hours=self.plan.duration_hours)
        super().save(*args, **kwargs)