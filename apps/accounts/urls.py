from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserActivityLogViewSet, PasswordResetRequestView, PasswordResetConfirmView, OnlineUsersView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'activity', UserActivityLogViewSet, basename='activity')

urlpatterns = [
    path('', include(router.urls)),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('online/', OnlineUsersView.as_view(), name='online-users'),
]