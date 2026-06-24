from django.urls import path, include
from .views import (
    SubnetViewSet, NetworkSettingsView, BandwidthLogViewSet,
    NetworkActivityView, SpeedTestView
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'subnets', SubnetViewSet, basename='subnet')
router.register(r'logs', BandwidthLogViewSet, basename='bandwidthlog')

urlpatterns = [
    path('settings/', NetworkSettingsView.as_view(), name='network-settings'),
    path('activity/', NetworkActivityView.as_view(), name='network-activity'),
    path('speedtest/', SpeedTestView.as_view(), name='speed-test'),
    path('', include(router.urls)),
]