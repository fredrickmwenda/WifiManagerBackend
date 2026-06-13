from rest_framework import serializers
from .models import Notification
from utils.whatsapp import generate_whatsapp_url

class NotificationSerializer(serializers.ModelSerializer):
    whatsapp_link = serializers.SerializerMethodField()
    is_new = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = '__all__'

    def get_whatsapp_link(self, obj):
        if obj.whatsapp_number:
            return generate_whatsapp_url(obj.whatsapp_number, obj.message)
        return None

    def get_is_new(self, obj):
        return obj.status == 'unread'