from rest_framework import serializers
from .models import Router

class RouterSerializer(serializers.ModelSerializer):
    bandwidth_usage_percent = serializers.SerializerMethodField()
    
    class Meta:
        model = Router
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'current_bandwidth_usage')

    def get_bandwidth_usage_percent(self, obj):
        if obj.bandwidth_limit > 0:
            return round((obj.current_bandwidth_usage / obj.bandwidth_limit) * 100, 1)
        return 0

class RouterListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Router
        fields = ['id', 'name', 'ip_address', 'status', 'model_name', 'location_tag', 'router_type']