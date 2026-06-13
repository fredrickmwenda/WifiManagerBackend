from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta
from .models import Subnet, NetworkSettings, BandwidthLog
from .serializers import SubnetSerializer, NetworkSettingsSerializer, BandwidthLogSerializer

class SubnetViewSet(viewsets.ModelViewSet):
    queryset = Subnet.objects.all()
    serializer_class = SubnetSerializer

class NetworkSettingsView(APIView):
    def get(self, request):
        settings = NetworkSettings.load()
        return Response(NetworkSettingsSerializer(settings).data)

    def post(self, request):
        settings = NetworkSettings.load()
        serializer = NetworkSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class BandwidthLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BandwidthLog.objects.all()
    serializer_class = BandwidthLogSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        router = self.request.query_params.get('router')
        if router:
            queryset = queryset.filter(router_id=router)
        return queryset

class NetworkActivityView(APIView):
    """
    Returns time-series data for the Real-Time Network Activity chart.
    """
    def get(self, request):
        minutes = int(request.query_params.get('minutes', 30))
        since = timezone.now() - timedelta(minutes=minutes)
        logs = BandwidthLog.objects.filter(timestamp__gte=since).order_by('timestamp')
        
        return Response({
            'labels': [l.timestamp.strftime('%H:%M:%S') for l in logs],
            'download': [round(l.download_mbps, 2) for l in logs],
            'upload': [round(l.upload_mbps, 2) for l in logs],
        })

class SpeedTestView(APIView):
    """
    Accepts or mocks speed test results (Ping/Download/Upload).
    In production, integrate with speedtest-cli or router APIs.
    """
    def post(self, request):
        # Store or simply return mock results
        data = {
            'ping_ms': request.data.get('ping', 12),
            'download_mbps': request.data.get('download', 85.5),
            'upload_mbps': request.data.get('upload', 42.3),
            'timestamp': timezone.now().isoformat()
        }
        return Response(data)