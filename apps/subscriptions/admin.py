from django.contrib import admin
from .models import SubscriptionPlan, Subscription, PaymentTransaction, Voucher, MPesaTransaction

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_ksh', 'duration_hours', 'is_active', 'created_at']
    list_filter = ['is_active']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['device', 'plan', 'status', 'start_time', 'end_time']
    list_filter = ['status', 'plan']

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_code', 'amount_ksh', 'channel', 'status', 'paid_at', 'created_at']
    list_filter = ['status', 'channel']

@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ['code', 'plan', 'is_used', 'used_at', 'expires_at']
    list_filter = ['is_used', 'plan']

@admin.register(MPesaTransaction)
class MPesaTransactionAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'amount', 'plan', 'status', 'mpesa_receipt_number', 'created_at']
    list_filter = ['status']
    search_fields = ['phone_number', 'checkout_request_id', 'mpesa_receipt_number']