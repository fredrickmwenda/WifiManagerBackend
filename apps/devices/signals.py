# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Device
# from apps.network.models import NetworkSettings
# from apps.notifications.models import Notification

# @receiver(post_save, sender=Device)
# def handle_new_device(sender, instance, created, **kwargs):
#     if created:
#         settings = NetworkSettings.load()
        
#         # Auto-block unknown
#         if settings.auto_block_unknown and not instance.is_whitelisted:
#             instance.status = 'blocked'
#             instance.save(update_fields=['status'])
        
#         # New device alert
#         if settings.new_device_alerts:
#             Notification.objects.create(
#                 notification_type='new_device',
#                 device=instance,
#                 title='New device connected',
#                 message=f'{instance.name} ({instance.ip_address}) connected to the network.',
#             )



from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Device
from apps.network.models import NetworkSettings
from apps.notifications.models import Notification
from apps.routers.models import RouterMacFilter
from apps.subscriptions.models import Subscription

@receiver(post_save, sender=Device)
def handle_new_device(sender, instance, created, **kwargs):
    if not created:
        return

    settings = NetworkSettings.load()
    router = instance.router

    # Layer 1: Global auto-block for unknown / non-whitelisted devices
    if settings.auto_block_unknown and not instance.is_whitelisted:
        instance.status = 'blocked'
        instance.save(update_fields=['status'])

        if settings.new_device_alerts:
            Notification.objects.create(
                notification_type='new_device',
                device=instance,
                title='Blocked unknown device',
                message=f'{instance.name} ({instance.ip_address}) was auto-blocked (not in whitelist).',
            )
        return

    # Layer 2: Paid router subscription enforcement with MAC bypass
    if router and router.access_mode == 'paid':
        has_active_sub = Subscription.objects.filter(
            device=instance,
            status='active',
            end_time__gt=timezone.now()
        ).exists()

        if not has_active_sub:
            # Check if this MAC is allowed to bypass subscription on this router
            mac_bypass = RouterMacFilter.objects.filter(
                router=router,
                mac_address__iexact=instance.mac_address,
                is_active=True,
                bypass_subscription=True
            ).exists()

            if not mac_bypass:
                instance.status = 'blocked'
                instance.save(update_fields=['status'])

                Notification.objects.create(
                    notification_type='subscription_expired',
                    device=instance,
                    title='Access denied - No subscription',
                    message=(
                        f'{instance.name} blocked on paid router {router.name}. '
                        f'No active subscription and MAC not in bypass list.'
                    ),
                    whatsapp_number=instance.phone_number,
                )
                return

    # Layer 3: Device is cleared for access
    if settings.new_device_alerts:
        Notification.objects.create(
            notification_type='new_device',
            device=instance,
            title='New device connected',
            message=f'{instance.name} ({instance.ip_address}) connected to {router.name if router else "network"}.',
        )