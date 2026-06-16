from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RouterViewSet, RouterMacFilterViewSet

# Register MAC filters FIRST to avoid URL collision with {pk}
router = DefaultRouter()
router.register(r'mac-filters', RouterMacFilterViewSet, basename='router-mac-filter')
router.register(r'', RouterViewSet, basename='router')

urlpatterns = [
    path('', include(router.urls)),
]
