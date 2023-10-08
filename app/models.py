from collections import defaultdict
from dataclasses import dataclass

import numpy as np
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from martor.models import MartorField
from pgvector.django import VectorField


class UserOwnedModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class LinkType(UserOwnedModel, TimeStampedModel):
    name = models.CharField(max_length=255)
    reverse_name = models.CharField(max_length=255, default='')

    class Meta:
        unique_together = ['user', 'name']
        ordering = ['name']


class Link(UserOwnedModel, TimeStampedModel):
    # Source generic foreign key fields
    source_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="source_links")
    source_object_id = models.PositiveIntegerField()
    source_content_object = GenericForeignKey('source_content_type', 'source_object_id')

    # Target generic foreign key fields
    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="target_links")
    target_object_id = models.PositiveIntegerField()
    target_content_object = GenericForeignKey('target_content_type', 'target_object_id')

    link_type = models.ForeignKey(LinkType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['source_content_type', 'source_object_id', 'target_content_type', 'target_object_id', 'link_type']
        ordering = ['link_type']


class NodeModel(UserOwnedModel, TimeStampedModel):
    title = models.CharField(max_length=255)
    content = MartorField()
    source_links = GenericRelation(Link, content_type_field='source_content_type', object_id_field='source_object_id', related_query_name='source')
    target_links = GenericRelation(Link, content_type_field='target_content_type', object_id_field='target_object_id', related_query_name='target')
    tags = models.ManyToManyField('Tag', blank=True)
    embedding = VectorField(dimensions=768, null=True)

    class Meta:
        abstract = True

    def create_tags(self, tags: list[str]):
        with transaction.atomic():
            # Create tags if they don't exist and collect them
            tag_objects = [
                Tag.objects.get_or_create(name=tag_name.lower(), user=self.user)[0] 
                for tag_name in tags
            ]
            
            # Associate all tags with the object in one go
            self.tags.add(*tag_objects)

    def all_links(self):
        content_type = ContentType.objects.get_for_model(self)
        return Link.objects.filter(
            models.Q(source_content_type=content_type, source_object_id=self.pk) |
            models.Q(target_content_type=content_type, target_object_id=self.pk)
        ).select_related('link_type')

    def get_link_groups(self) -> dict[tuple[LinkType, str], list['NodeModel']]:
        link_groups = defaultdict(list)
        for link in self.all_links():
            direction = "outgoing" if link.source_content_object == self else "incoming"
            key = (link.link_type, direction)
            target = link.target_content_object if direction == "outgoing" else link.source_content_object
            link_groups[key].append(target)
        return dict(link_groups)


class Memo(NodeModel):
    class Meta:
        ordering = ['-created_at']


class Reference(NodeModel):
    source_url = models.URLField(max_length=2000, blank=True, null=True)
    source_name = models.CharField(max_length=255, blank=True, null=True)
    publication_date = models.DateField(blank=True, null=True)
    authors = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']


class Inkling(NodeModel):
    class Meta:
        ordering = ['-created_at']


class Tag(UserOwnedModel, TimeStampedModel):
    name = models.CharField(max_length=50)
    embedding = VectorField(dimensions=768, null=True)

    def save(self, *args, **kwargs):
        self.name = self.name.lower().strip()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['user', 'name']
        ordering = ['name']

    def __str__(self):
        return self.name

@dataclass
class Query:
    query: str
    embedding: np.ndarray
