from django.db import models


class Router(models.Model):
    ROUTER_TYPES = [
        ("tp-link", "TP-Link"),
        ("mikrotik", "MikroTik"),
        ("cisco", "Cisco"),
        ("huawei", "Huawei"),
        ("ubiquiti", "Ubiquiti"),
        ("generic", "Generic"),
    ]
    ACCESS_MODES = [
        ("paid", "Paid (subscription required)"),
        ("free", "Free Access"),
    ]
    PROTOCOLS = [
        ("http", "HTTP"),
        ("https", "HTTPS"),
    ]
    STATUS_CHOICES = [
        ("online", "Online"),
        ("offline", "Offline"),
        ("rebooting", "Rebooting"),
    ]

    name = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100, blank=True, verbose_name="Model")
    location_tag = models.CharField(
        max_length=100, blank=True, help_text="e.g. Nairobi - HQ"
    )
    router_type = models.CharField(max_length=20, choices=ROUTER_TYPES, default="generic")
    access_mode = models.CharField(max_length=10, choices=ACCESS_MODES, default="paid")
    ip_address = models.GenericIPAddressField()
    port = models.PositiveIntegerField(default=80)
    username = models.CharField(max_length=100, blank=True)
    password = models.CharField(max_length=100, blank=True)
    protocol = models.CharField(max_length=5, choices=PROTOCOLS, default="http")
    ssid = models.CharField(max_length=100, blank=True)
    wlan_key = models.CharField(max_length=100, blank=True)
    mac_address = models.CharField(max_length=17, blank=True)
    firmware = models.CharField(max_length=50, blank=True)
    uptime = models.CharField(max_length=50, blank=True, help_text="e.g. 14d 6h 23m")
    bandwidth_limit = models.PositiveIntegerField(default=200, help_text="Mbps")
    current_bandwidth_usage = models.FloatField(default=0, help_text="Mbps")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="offline")
    is_active_setup = models.BooleanField(
        default=False, help_text="Active Router Setup"
    )

    # Connector / sync fields
    last_synced_at = models.DateTimeField(null=True, blank=True)
    connection_status = models.CharField(
        max_length=20,
        default="unknown",
        choices=[
            ("connected", "Connected"),
            ("failed", "Failed"),
            ("unknown", "Unknown"),
            ("syncing", "Syncing"),
        ],
    )
    connection_error = models.TextField(blank=True)
    api_version = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.ip_address})"


class RouterMacFilter(models.Model):
    router = models.ForeignKey(
        Router, on_delete=models.CASCADE, related_name="mac_filters"
    )
    mac_address = models.CharField(max_length=17, db_index=True)
    name = models.CharField(max_length=100, blank=True, help_text="e.g. Office Printer")
    is_active = models.BooleanField(default=True)
    bypass_subscription = models.BooleanField(
        default=True,
        help_text="Allow access without subscription on paid routers",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["router", "mac_address"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.mac_address} ({self.router.name})"


class RouterSyncLog(models.Model):
    ACTION_CHOICES = [
        ("sync", "Sync"),
        ("reboot", "Reboot"),
        ("discover", "Discover Devices"),
        ("apply_wifi", "Apply WiFi"),
        ("block_mac", "Block MAC"),
        ("unblock_mac", "Unblock MAC"),
        ("bandwidth_limit", "Bandwidth Limit"),
    ]
    STATUS_CHOICES = [
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    router = models.ForeignKey(
        Router, on_delete=models.CASCADE, related_name="sync_logs"
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    message = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.router.name} — {self.action} ({self.status})"