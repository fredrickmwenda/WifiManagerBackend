from django.db import models
from utils.models import SingletonModel

class Subnet(models.Model):
    name = models.CharField(max_length=100)
    ip_range = models.CharField(max_length=50, help_text='CIDR, e.g. 192.168.1.0/24')
    gateway = models.GenericIPAddressField()
    ips_used = models.PositiveIntegerField(default=0)
    ips_total = models.PositiveIntegerField(default=254)
    router = models.ForeignKey('routers.Router', on_delete=models.CASCADE, related_name='subnets', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.ip_range})"


class NetworkSettings(SingletonModel):
    global_bandwidth_cap = models.PositiveIntegerField(default=100, help_text='Mbps')
    qos_enabled = models.BooleanField(default=True, verbose_name='QoS (Quality of Service)')
    guest_network_enabled = models.BooleanField(default=False, verbose_name='Guest Network')
    auto_block_unknown = models.BooleanField(default=False, verbose_name='Auto-Block Unknown Devices')
    mac_filtering_enabled = models.BooleanField(default=True, verbose_name='MAC Address Filtering')
    intrusion_detection_enabled = models.BooleanField(default=True, verbose_name='Intrusion Detection')
    new_device_alerts = models.BooleanField(default=True, verbose_name='New Device Alerts')
    bandwidth_alerts = models.BooleanField(default=True, verbose_name='Bandwidth Alerts')
    alert_email = models.EmailField(blank=True)

    class Meta:
        verbose_name = 'Network Settings'
        verbose_name_plural = 'Network Settings'


class BandwidthLog(models.Model):
    router = models.ForeignKey('routers.Router', on_delete=models.CASCADE, related_name='bandwidth_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    download_mbps = models.FloatField(default=0)
    upload_mbps = models.FloatField(default=0)
    total_mbps = models.FloatField(default=0)

    class Meta:
        ordering = ['-timestamp']