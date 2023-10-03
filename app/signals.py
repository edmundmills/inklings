from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Tag


@receiver(post_save, sender=User)
def create_default_keywords(sender, instance, created, **kwargs):
    if created:
        for tag_name in Tag.DEFAULT_TAGS:
            Tag.objects.create(name=tag_name, user=instance)
