from django.db import models

class Router(models.Model):
    ROUTER_TYPES = [
        ('tp-link', 'TP-Link'),
        ('mikrotik', 'MikroTik'),
        ('ubiquiti', 'Ubiquiti'),
        ('generic', 'Generic'),
    ]
    ACCESS_MODES = [
        ('paid', 'Paid (subscription required)'),
        ('free', 'Free Access'),
    ]
    PROTOCOLS = [
        ('http', 'HTTP'),
        ('https', 'HTTPS'),
    ]
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('rebooting', 'Rebooting'),
    ]

    name = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100, blank=True, verbose_name='Model')
    location_tag = models.CharField(max_length=100, blank=True, help_text='e.g. Nairobi - HQ')
    router_type = models.CharField(max_length=20, choices=ROUTER_TYPES, default='tp-link')
    access_mode = models.CharField(max_length=10, choices=ACCESS_MODES, default='paid')
    ip_address = models.GenericIPAddressField()
    port = models.PositiveIntegerField(default=80)
    username = models.CharField(max_length=100, blank=True)
    password = models.CharField(max_length=100, blank=True)
    protocol = models.CharField(max_length=5, choices=PROTOCOLS, default='http')
    ssid = models.CharField(max_length=100, blank=True)
    wlan_key = models.CharField(max_length=100, blank=True)
    mac_address = models.CharField(max_length=17, blank=True)
    firmware = models.CharField(max_length=50, blank=True)
    uptime = models.CharField(max_length=50, blank=True, help_text='e.g. 14d 6h 23m')
    bandwidth_limit = models.PositiveIntegerField(default=200, help_text='Mbps')
    current_bandwidth_usage = models.FloatField(default=0, help_text='Mbps')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='offline')
    is_active_setup = models.BooleanField(default=False, help_text='Active Router Setup')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.ip_address})"