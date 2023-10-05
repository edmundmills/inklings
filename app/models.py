from django.contrib.auth.models import User
from django.db import models
from martor.models import MartorField
from pgvector.django import VectorField


class Memo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = MartorField()
    tags = models.ManyToManyField('Tag', blank=True)
    embedding = VectorField(dimensions=768, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Inkling(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    memo = models.ForeignKey(Memo, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    embedding = VectorField(dimensions=768, null=True)
    tags = models.ManyToManyField('Tag', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Tag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    embedding = VectorField(dimensions=768, null=True)

    DEFAULT_TAGS = ['Task', 'Idea', 'Social', 'Family', 'Craft', 'Reflection', 'Health', 'Event', 'Work']

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['user', 'name']
    
    def __str__(self):
        return self.name


class LinkType(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    reverse_name = models.CharField(max_length=255, default='')
    DEFAULT_LINK_TYPES = [('Supporting', 'Supported by'), ('Counterargument against', 'Countered by'), ('Elaboration for', 'Elaborated by'), ('Inspiration for', 'Inspired by'), ('Next Step', 'Previous Step'),('Related Question', 'Question about'), ('Summary for', 'Summarized by')]

    class Meta:
        unique_together = ['user', 'name']


class Link(models.Model):
    source_inkling = models.ForeignKey('Inkling', on_delete=models.CASCADE, related_name='source_links')
    target_inkling = models.ForeignKey('Inkling', on_delete=models.CASCADE, related_name='target_links')
    link_type = models.ForeignKey(LinkType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['source_inkling', 'target_inkling', 'link_type']
