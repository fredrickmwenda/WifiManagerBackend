from django.db import models

class Notification(models.Model):
    TYPE_CHOICES = [
        ('subscription_expired', 'Subscription Expired'),
        ('subscription_expiring', 'Subscription Expiring Soon'),
        ('new_device', 'New Device'),
        ('bandwidth_alert', 'Bandwidth Alert'),
        ('intrusion', 'Intrusion Detected'),
    ]
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
    ]

    notification_type = models.CharField(max_length=25, choices=TYPE_CHOICES)  # <-- changed from 20
    device = models.ForeignKey('devices.Device', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    whatsapp_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unread')
    sent_via_whatsapp = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title