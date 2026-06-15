from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('api/accounts/', include('apps.accounts.urls')),    
    path('api/auth/', include('rest_framework.urls')),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/routers/', include('apps.routers.urls')),
    path('api/devices/', include('apps.devices.urls')),
    path('api/network/', include('apps.network.urls')),
    path('api/subscriptions/', include('apps.subscriptions.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
]