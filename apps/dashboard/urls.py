from django.urls import path
from .views import DashboardStatsView, DashboardChartView

urlpatterns = [
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('chart/', DashboardChartView.as_view(), name='dashboard-chart'),
]