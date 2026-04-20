from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_profile_for_user(sender, instance, created, **kwargs):
    if created:
        full_name = instance.get_full_name() or instance.username
        Profile.objects.create(
            user=instance,
            full_name=full_name,
            email=instance.email or "",
            role=Profile.ROLE_TEACHER,
        )


@receiver(post_save, sender=User)
def save_profile_for_user(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.email = instance.email or instance.profile.email
        instance.profile.save()
