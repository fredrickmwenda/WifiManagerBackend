from rest_framework import serializers
from .models import Device
from apps.subscriptions.models import Subscription

class DeviceSerializer(serializers.ModelSerializer):
    subscription_plan = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = '__all__'

    def get_subscription_plan(self, obj):
        active = obj.subscriptions.filter(status='active').first()
        if active:
            return {
                'id': active.plan.id,
                'name': active.plan.name,
                'color': active.plan.color,
                'price_ksh': active.plan.price_ksh,
            }
        return None

    def get_subscription_status(self, obj):
        active = obj.subscriptions.filter(status='active').first()
        return active.status if active else 'no_plan'