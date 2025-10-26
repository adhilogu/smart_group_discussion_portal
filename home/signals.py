from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile  # Import your model

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            name=instance.first_name if instance.first_name else instance.username,  # Use first name if available
            mail_id=instance.email,  # Set email
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.name = instance.first_name if instance.first_name else instance.username
    instance.userprofile.mail_id = instance.email
    instance.userprofile.save()

