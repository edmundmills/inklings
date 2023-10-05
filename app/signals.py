from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .helpers import generate_embedding
from .models import Inkling, LinkType, Memo, Tag


@receiver(post_save, sender=User)
def create_default_keywords(sender, instance, created, **kwargs):
    if created:
        for tag_name in Tag.DEFAULT_TAGS:
            Tag.objects.create(name=tag_name, user=instance)
        for link_type in LinkType.DEFAULT_LINK_TYPES:
            LinkType.objects.create(name=link_type, user=instance)

@receiver(post_save, sender=Inkling)
def generate_and_save_embedding_for_inkling(sender, instance, **kwargs):
    if instance.embedding is None:
        instance.embedding = generate_embedding(instance.content)
        instance.save(update_fields=['embedding'])

@receiver(post_save, sender=Memo)
def generate_and_save_embedding_for_memo(sender, instance, **kwargs):
    if instance.embedding is None:
        instance.embedding = generate_embedding(f'{instance.title}: {instance.content}')
        instance.save(update_fields=['embedding'])

@receiver(post_save, sender=Tag)
def generate_and_save_embedding_for_tag(sender, instance, **kwargs):
    if instance.embedding is None:
        instance.embedding = generate_embedding(instance.name)
        instance.save(update_fields=['embedding'])
