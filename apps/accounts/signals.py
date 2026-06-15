from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import User, UserActivityLog


@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    if created and instance.created_by:
        UserActivityLog.objects.create(
            user=instance.created_by,
            action='settings_change',
            details={'message': f'Created user {instance.username} with role {instance.role}'}
        )