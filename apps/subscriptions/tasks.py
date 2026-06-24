from celery import shared_task
from django.utils import timezone
from .models import Subscription
from apps.notifications.models import Notification

@shared_task
def check_subscription_expiry():
    now = timezone.now()
    
    # Mark expired
    expired = Subscription.objects.filter(end_time__lte=now, status='active')
    for sub in expired:
        sub.status = 'expired'
        sub.save()
        
        # Use the phone number from M-Pesa payment (stored on device)
        phone = sub.device.phone_number if sub.device else ''
        
        Notification.objects.create(
            notification_type='subscription_expired',
            device=sub.device,
            title='Subscription expired',
            message=f'{sub.device.name} — {sub.plan.name} plan expired.',
            whatsapp_number=phone,  # This comes from M-Pesa
        )

    # Expiring soon (30 mins)
    soon_window = now + timezone.timedelta(minutes=30)
    expiring = Subscription.objects.filter(
        end_time__lte=soon_window,
        end_time__gt=now,
        status='active'
    )
    for sub in expiring:
        exists = Notification.objects.filter(
            device=sub.device,
            notification_type='subscription_expiring',
            created_at__gte=now - timezone.timedelta(hours=1)
        ).exists()
        if not exists:
            phone = sub.device.phone_number if sub.device else ''
            Notification.objects.create(
                notification_type='subscription_expiring',
                device=sub.device,
                title='Subscription expiring soon',
                message=f'{sub.device.name} — {sub.plan.name} plan expires in 30 minutes.',
                whatsapp_number=phone,  # This comes from M-Pesa
            )



# from celery import shared_task
# from django.utils import timezone
# from .models import Subscription
# from apps.notifications.models import Notification

# @shared_task
# def check_subscription_expiry():
#     now = timezone.now()
    
#     # Mark expired
#     expired = Subscription.objects.filter(end_time__lte=now, status='active')
#     for sub in expired:
#         sub.status = 'expired'
#         sub.save()
#         Notification.objects.create(
#             notification_type='subscription_expired',
#             device=sub.device,
#             title='Subscription expired',
#             message=f'{sub.device.name} — {sub.plan.name} plan expired.',
#             whatsapp_number=sub.device.phone_number,
#         )

#     # Expiring soon (30 mins)
#     soon_window = now + timezone.timedelta(minutes=30)
#     expiring = Subscription.objects.filter(
#         end_time__lte=soon_window,
#         end_time__gt=now,
#         status='active'
#     )
#     for sub in expiring:
#         exists = Notification.objects.filter(
#             device=sub.device,
#             notification_type='subscription_expiring',
#             created_at__gte=now - timezone.timedelta(hours=1)
#         ).exists()
#         if not exists:
#             Notification.objects.create(
#                 notification_type='subscription_expiring',
#                 device=sub.device,
#                 title='Subscription expiring soon',
#                 message=f'{sub.device.name} — {sub.plan.name} plan expires in 30 minutes.',
#                 whatsapp_number=sub.device.phone_number,
            # )