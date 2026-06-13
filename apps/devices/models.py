from django.db import models

class Device(models.Model):
    STATUS_CHOICES = [
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('blocked', 'Blocked'),
    ]
    DEVICE_TYPES = [
        ('phone', 'Phone'),
        ('laptop', 'Laptop'),
        ('tv', 'TV'),
        ('tablet', 'Tablet'),
        ('gaming', 'Gaming'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=17, unique=True)
    router = models.ForeignKey('routers.Router', on_delete=models.CASCADE, related_name='devices')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='connected')
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPES, default='other')
    data_usage_mb = models.FloatField(default=0)
    bandwidth_mbps = models.FloatField(default=0)
    bandwidth_cap = models.FloatField(default=0, help_text='0 = no cap')
    is_whitelisted = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True, help_text='For WhatsApp alerts')
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_seen']

    def __str__(self):
        return f"{self.name} ({self.ip_address})"