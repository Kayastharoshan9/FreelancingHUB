from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

# Signal to create a user profile when a user is created
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(
            user=instance,
            username=instance.username,
            email=instance.email,
            name=instance.first_name + ' ' + instance.last_name if instance.first_name else instance.username,
        )
        profile.save()

# Signal to update user when profile is updated
@receiver(post_save, sender=Profile)
def update_user(sender, instance, created, **kwargs):
    if not created:
        user = instance.user
        if user:
            user.first_name = instance.name.split()[0] if instance.name else ''
            user.last_name = ' '.join(instance.name.split()[1:]) if instance.name and len(instance.name.split()) > 1 else ''
            user.email = instance.email
            user.username = instance.username
            user.save()

# Delete user when profile is deleted
@receiver(post_delete, sender=Profile)
def delete_user(sender, instance, **kwargs):
    try:
        user = instance.user
        if user:
            user.delete()
    except:
        pass