from rest_framework import serializers
from .models import SubscriptionPlan, Subscription

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.name', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_color = serializers.CharField(source='plan.color', read_only=True)
    time_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = ('start_time', 'end_time', 'status')

    def get_time_remaining(self, obj):
        from django.utils import timezone
        remaining = obj.end_time - timezone.now()
        if remaining.total_seconds() > 0:
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            return f"{hours}h {minutes}m"
        return "0m"