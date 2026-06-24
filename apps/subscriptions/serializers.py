from rest_framework import serializers
from .models import SubscriptionPlan, Subscription, PaymentTransaction, Voucher, MPesaTransaction


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


class PaymentTransactionSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='subscription.device.name', read_only=True)
    plan_name = serializers.CharField(source='subscription.plan.name', read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = '__all__'
        read_only_fields = ['paid_at', 'created_at']


class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = '__all__'
        read_only_fields = ['is_used', 'used_by', 'used_at', 'created_at']


class MPesaTransactionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)

    class Meta:
        model = MPesaTransaction
        fields = '__all__'
        read_only_fields = [
            'checkout_request_id', 'merchant_request_id', 'mpesa_receipt_number',
            'result_code', 'result_desc', 'status', 'raw_callback', 'created_at', 'updated_at'
        ]


class STKPushRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True, max_length=20)
    plan_id = serializers.IntegerField(required=True)
    device_mac = serializers.CharField(required=True, max_length=17)


class MPesaCallbackSerializer(serializers.Serializer):
    Body = serializers.DictField()


class SubscriptionAnalyticsSerializer(serializers.Serializer):
    total_revenue = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    expired_today = serializers.IntegerField()
    popular_plan = serializers.CharField()
    vouchers_redeemed = serializers.IntegerField()