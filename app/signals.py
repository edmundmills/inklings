from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .embeddings import generate_embedding
from .models import Inkling, Link, LinkType, Memo, Reference, Tag, UserProfile


@receiver(post_save, sender=User)
def create_default_keywords(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()


@receiver(post_save, sender=Inkling)
def generate_and_save_embedding_for_inkling(sender, instance, **kwargs):
    if instance.embedding is None:
        instance.embedding = generate_embedding(instance.content, instance.title)
        instance.save(update_fields=['embedding'])

@receiver(post_save, sender=Link)
def generate_and_save_embedding_for_link(sender, instance, **kwargs):
    if instance.embedding is None:
        instance.embedding = (0.2 * generate_embedding(instance.link_type.name, instance.link_type.reverse_name)) + (0.4* instance.source_content_object.embedding) + (0.4 * instance.target_content_object.embedding)
        instance.save(update_fields=['embedding'])

@receiver(post_save, sender=Memo)
def generate_and_save_embedding_for_memo(sender, instance, **kwargs):
    if instance.embedding is None:
        instance.embedding = generate_embedding(instance.content, instance.title)
        instance.save(update_fields=['embedding'])

@receiver(post_save, sender=Reference)
def generate_and_save_embedding_for_reference(sender, instance, **kwargs):
    if instance.embedding is None:
        instance.embedding = generate_embedding(instance.content, instance.title)
        instance.save(update_fields=['embedding'])

@receiver(post_save, sender=Tag)
def generate_and_save_embedding_for_tag(sender, instance, **kwargs):
    if instance.embedding is None:
        instance.embedding = generate_embedding(instance.name)
        instance.save(update_fields=['embedding'])
