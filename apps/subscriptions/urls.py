from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubscriptionPlanViewSet,
    SubscriptionViewSet,
    PaymentTransactionViewSet,
    VoucherViewSet,
    SubscriptionAnalyticsView,
    MPesaPaymentViewSet,
    mpesa_callback,
)

router = DefaultRouter()
router.register(r'plans', SubscriptionPlanViewSet, basename='plan')
router.register(r'', SubscriptionViewSet, basename='subscription')
router.register(r'payments', PaymentTransactionViewSet, basename='payment')
router.register(r'vouchers', VoucherViewSet, basename='voucher')
router.register(r'mpesa', MPesaPaymentViewSet, basename='mpesa')

urlpatterns = [
    path('', include(router.urls)),
    path('analytics/', SubscriptionAnalyticsView.as_view(), name='subscription-analytics'),
    path('mpesa/callback/', mpesa_callback, name='mpesa-callback'),
]