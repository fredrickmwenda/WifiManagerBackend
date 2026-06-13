from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Max, Count, Q
from django.utils import timezone
from datetime import timedelta

from apps.devices.models import Device
from apps.routers.models import Router
from apps.subscriptions.models import Subscription
from apps.network.models import BandwidthLog, NetworkSettings

class DashboardStatsView(APIView):
    def get(self, request):
        total_devices = Device.objects.count()
        connected = Device.objects.filter(status='connected').count()
        blocked = Device.objects.filter(status='blocked').count()
        total_data = Device.objects.aggregate(t=Sum('data_usage_mb'))['t'] or 0
        active_subs = Subscription.objects.filter(status='active').count()
        
        latest_log = BandwidthLog.objects.order_by('-timestamp').first()
        current_bw = round(latest_log.total_mbps, 2) if latest_log else 0
        peak = BandwidthLog.objects.aggregate(p=Max('total_mbps'))['p'] or 0
        
        # Routers
        online_routers = Router.objects.filter(status='online').count()
        
        # Recent peak usage timestamp
        peak_log = BandwidthLog.objects.filter(total_mbps=peak).order_by('-timestamp').first()
        peak_time = peak_log.timestamp.strftime('%d %b, %I:%M %p') if peak_log else None

        return Response({
            'connected_devices': connected,
            'total_devices': total_devices,
            'blocked_devices': blocked,
            'total_data_used_gb': round(total_data / 1024, 2),
            'active_subscriptions': active_subs,
            'current_bandwidth_mbps': current_bw,
            'peak_usage_mbps': round(peak, 2),
            'peak_usage_time': peak_time,
            'online_routers': online_routers,
        })

class DashboardChartView(APIView):
    """
    Feeds the Real-Time Network Activity area chart.
    """
    def get(self, request):
        minutes = int(request.query_params.get('span', 30))
        since = timezone.now() - timedelta(minutes=minutes)
        logs = BandwidthLog.objects.filter(timestamp__gte=since).order_by('timestamp')
        
        return Response({
            'labels': [l.timestamp.strftime('%H:%M:%S') for l in logs],
            'download': [round(l.download_mbps, 2) for l in logs],
            'upload': [round(l.upload_mbps, 2) for l in logs],
        })