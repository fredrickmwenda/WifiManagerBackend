from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from utils.whatsapp import generate_whatsapp_url
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'notification_type']
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().filter(status='unread').update(status='read')
        return Response({'detail': 'All notifications marked as read.'})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.status = 'read'
        notif.save()
        return Response({'detail': 'Marked as read.'})

    @action(detail=True, methods=['post'])
    def send_whatsapp(self, request, pk=None):
        notif = self.get_object()
        if notif.whatsapp_number:
            notif.sent_via_whatsapp = True
            notif.save()
            return Response({
                'whatsapp_url': generate_whatsapp_url(notif.whatsapp_number, notif.message)
            })
        return Response({'error': 'No phone number available.'}, status=status.HTTP_400_BAD_REQUEST)