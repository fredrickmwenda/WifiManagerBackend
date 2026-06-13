from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Device
from apps.network.models import NetworkSettings
from apps.notifications.models import Notification

@receiver(post_save, sender=Device)
def handle_new_device(sender, instance, created, **kwargs):
    if created:
        settings = NetworkSettings.load()
        
        # Auto-block unknown
        if settings.auto_block_unknown and not instance.is_whitelisted:
            instance.status = 'blocked'
            instance.save(update_fields=['status'])
        
        # New device alert
        if settings.new_device_alerts:
            Notification.objects.create(
                notification_type='new_device',
                device=instance,
                title='New device connected',
                message=f'{instance.name} ({instance.ip_address}) connected to the network.',
            )