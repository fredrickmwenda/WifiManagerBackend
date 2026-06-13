from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Router
from .serializers import RouterSerializer, RouterListSerializer

class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'router_type', 'access_mode']
    search_fields = ['name', 'ip_address', 'location_tag']

    def get_serializer_class(self):
        if self.action == 'list':
            return RouterListSerializer
        return RouterSerializer

    @action(detail=True, methods=['post'])
    def restart(self, request, pk=None):
        router = self.get_object()
        router.status = 'rebooting'
        router.save()
        # In production: trigger async router restart via SSH/API
        return Response({'detail': 'Restart command issued.'}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'])
    def set_active(self, request, pk=None):
        Router.objects.update(is_active_setup=False)
        router = self.get_object()
        router.is_active_setup = True
        router.save()
        return Response({'detail': f'{router.name} is now the active router.'})