from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Device
from .serializers import DeviceSerializer

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'router', 'device_type']
    search_fields = ['name', 'ip_address', 'mac_address']

    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        device = self.get_object()
        device.status = 'blocked'
        device.save()
        return Response({'detail': f'{device.name} blocked.'})

    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        device = self.get_object()
        device.status = 'connected'
        device.save()
        return Response({'detail': f'{device.name} unblocked.'})