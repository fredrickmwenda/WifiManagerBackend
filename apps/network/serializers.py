from rest_framework import serializers
from .models import Subnet, NetworkSettings, BandwidthLog

class SubnetSerializer(serializers.ModelSerializer):
    utilization_percent = serializers.SerializerMethodField()
    
    class Meta:
        model = Subnet
        fields = '__all__'

    def get_utilization_percent(self, obj):
        if obj.ips_total > 0:
            return round((obj.ips_used / obj.ips_total) * 100, 1)
        return 0

class NetworkSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkSettings
        fields = '__all__'

class BandwidthLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BandwidthLog
        fields = '__all__'