from rest_framework import serializers
from .models import Router, RouterMacFilter, RouterSyncLog


class RouterMacFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouterMacFilter
        fields = "__all__"
        read_only_fields = ["created_at"]


class RouterSyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouterSyncLog
        fields = ["id", "action", "status", "message", "details", "created_at"]


class RouterSerializer(serializers.ModelSerializer):
    bandwidth_usage_percent = serializers.SerializerMethodField()
    mac_filters = RouterMacFilterSerializer(many=True, read_only=True)
    bypass_mac_count = serializers.SerializerMethodField()
    recent_sync_logs = serializers.SerializerMethodField()

    class Meta:
        model = Router
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
            "current_bandwidth_usage",
            "last_synced_at",
            "connection_status",
            "connection_error",
        )

    def get_bandwidth_usage_percent(self, obj):
        if obj.bandwidth_limit > 0:
            return round((obj.current_bandwidth_usage / obj.bandwidth_limit) * 100, 1)
        return 0

    def get_bypass_mac_count(self, obj):
        return obj.mac_filters.filter(is_active=True, bypass_subscription=True).count()

    def get_recent_sync_logs(self, obj):
        logs = obj.sync_logs.order_by("-created_at")[:5]
        return RouterSyncLogSerializer(logs, many=True).data


class RouterListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Router
        fields = [
            "id",
            "name",
            "ip_address",
            "status",
            "connection_status",
            "model_name",
            "location_tag",
            "router_type",
            "access_mode",
        ]