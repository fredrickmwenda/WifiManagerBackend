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

class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    CHANNEL_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('cash', 'Cash'),
        ('voucher', 'Voucher'),
    ]

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    amount_ksh = models.PositiveIntegerField()
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    transaction_code = models.CharField(max_length=100, blank=True, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    phone_number = models.CharField(max_length=20, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Voucher(models.Model):
    code = models.CharField(max_length=20, unique=True, db_index=True)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='vouchers')
    is_used = models.BooleanField(default=False)
    used_by = models.ForeignKey('devices.Device', on_delete=models.SET_NULL, null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code

class MPesaTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    phone_number = models.CharField(max_length=20)
    amount = models.PositiveIntegerField()
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='mpesa_payments')
    device_mac = models.CharField(max_length=17, blank=True, db_index=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, db_index=True)
    merchant_request_id = models.CharField(max_length=100, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True, db_index=True)
    transaction_date = models.CharField(max_length=50, blank=True)
    result_code = models.CharField(max_length=10, blank=True)
    result_desc = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    raw_callback = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.phone_number} - KSH {self.amount} ({self.status})"