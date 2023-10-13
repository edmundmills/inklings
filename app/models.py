import uuid
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import numpy as np
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from martor.models import MartorField
from pgvector.django import CosineDistance, VectorField


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser, TimeStampedModel):
    email = models.EmailField(unique=True)
    friends = models.ManyToManyField('self', blank=True, symmetrical=True)
    intention = models.TextField(blank=True, null=True)
    intention_embedding = VectorField(dimensions=384, null=True)

    class Meta:
        abstract = False

    def send_friend_request(self, receiver: 'User'):
        if not self.has_sent_request_to(receiver) and not self.is_friends_with(receiver):
            FriendRequest.objects.create(sender=self, receiver=receiver)

    def accept_friend_request(self, sender: 'User'):
        if sender.has_sent_request_to(self):
            self.friends.add(sender)
            sender.friends.add(self)
            FriendRequest.objects.filter(sender=sender, receiver=self).delete()

    def reject_friend_request(self, sender: 'User'):
        FriendRequest.objects.filter(sender=sender, receiver=self).delete()

    def remove_friend(self, friend: 'User'):
        self.friends.remove(friend)

    def is_friends_with(self, friend: 'User'):
        return friend in self.friends.all()

    def has_sent_request_to(self, receiver: 'User'):
        return FriendRequest.objects.filter(sender=self, receiver=receiver).exists()



class FriendRequest(TimeStampedModel):
    sender = models.ForeignKey(User, related_name="sent_requests", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="incoming_requests", on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['sender', 'receiver']
        pass

    @classmethod
    def has_request_from_to(cls, sender, receiver):
        return cls.objects.filter(sender=sender, receiver=receiver).exists()



class UserOwnedModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class PrivacySettingsModel(UserOwnedModel):
    PRIVATE = 'private'
    FRIENDS = 'friends'
    FRIENDS_OF_FRIENDS = 'friends_of_friends'

    PRIVACY_CHOICES = [
        (PRIVATE, 'Private'),
        (FRIENDS, 'Friends'),
        (FRIENDS_OF_FRIENDS, 'Friends of Friends'),
    ]

    privacy_setting = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default=PRIVATE)

    class Meta:
        abstract = True


    def is_viewable_by(self, user):
        """
        Determine if a model instance is viewable by the given user based on privacy settings.
        """
        # If the object belongs to the user, they can always view it
        if self.user == user:
            return True

        # If privacy is set to private, only the owner can view
        if self.privacy_setting == self.PRIVATE:
            return False

        # If privacy is set to friends, check if the given user is a friend of the owner
        if self.privacy_setting == self.FRIENDS:
            return user.is_friends_with(self.user) # type: ignore

        # If privacy is set to friends of friends, check the relationship accordingly
        if self.privacy_setting == self.FRIENDS_OF_FRIENDS:
            # Direct friends
            if user.is_friends_with(self.user):  # type: ignore
                return True
            
            # Friends of friends
            user_friends = user.friends.all()
            owner_friends = self.user.friends.all() # type: ignore
            
            # Intersection checks for mutual friends
            mutual_friends = set(user_friends).intersection(owner_friends)
            return bool(mutual_friends)

        return False


    @classmethod
    def _get_own_objects_filter(cls, user) -> Q:
        """
        Return a Q object representing objects that are owned by the given user.
        """
        return Q(user=user)

    @classmethod
    def _get_friends_objects_filter(cls, user) -> Q:
        """
        Return a Q object representing objects owned by the friends of the given user.
        """
        return Q(privacy_setting=cls.FRIENDS, user__friends=user) | Q(privacy_setting=cls.FRIENDS_OF_FRIENDS, user__friends=user)

    @classmethod
    def _get_friends_of_friends_objects_filter(cls, user) -> Q:
        """
        Return a Q object representing objects owned by the friends of friends of the given user.
        """
        user_friends = user.friends.all()
        return Q(privacy_setting=cls.FRIENDS_OF_FRIENDS, user__friends__in=user_friends) & ~Q(user__in=user_friends)

    @classmethod
    def get_privacy_filter(cls, user, level) -> Q:
        """
        Return a combined Q object based on the level:
        - 'own': Just the user's objects.
        - 'friends': User's and friends' objects.
        - 'fof': User's, friends', and friends of friends' objects.
        """
        if level == 'own':
            return cls._get_own_objects_filter(user)
        elif level == 'friends':
            return cls._get_own_objects_filter(user) | cls._get_friends_objects_filter(user)
        elif level == 'fof':
            return cls._get_own_objects_filter(user) | cls._get_friends_objects_filter(user) | cls._get_friends_of_friends_objects_filter(user)
        else:
            raise ValueError("Invalid level provided.")



class TitleAndContentModel(models.Model):
    title = models.CharField(max_length=255)
    content = MartorField()

    class Meta:
        abstract = True


class SummarizableModel(models.Model):
    summary = models.CharField(max_length=1024)

    class Meta:
        abstract = True


class LinkType(UserOwnedModel, TimeStampedModel):
    name = models.CharField(max_length=255)
    reverse_name = models.CharField(max_length=255, default='')

    class Meta:
        unique_together = ['user', 'name']
        ordering = ['name']

    @classmethod
    def get_list_url(cls):
        return reverse('link_types')


class EmbeddableModel(models.Model):
    embedding = VectorField(dimensions=384, null=True)

    class Meta:
        abstract = True

    @classmethod
    def get_similar_objects(cls, embedding, user: User, 
                            exclude_filter: Optional[Q] = None,
                            limit: Optional[int] = None,
                            distance_threshold: float = 0.6,
                            privacy_level: str = 'own') -> models.QuerySet:

        queryset = (cls.objects
                    .alias(distance=CosineDistance('embedding', embedding))
                    .filter(distance__lt=distance_threshold)
                    .order_by('distance'))
    
        if issubclass(cls, PrivacySettingsModel):
            privacy_filter = cls.get_privacy_filter(user, privacy_level)
        else:
            privacy_filter = Q(user=user)
        queryset = queryset.filter(privacy_filter)

        
        if exclude_filter is not None:
            queryset = queryset.exclude(exclude_filter)
            
        if limit:
            queryset = queryset[:limit]
            
        return queryset


class TaggableModel(UserOwnedModel):
    tags = models.ManyToManyField('Tag', blank=True)

    def create_tags(self, tags: list[str]):
        with transaction.atomic():
            tag_objects = [
                Tag.objects.get_or_create(name=tag_name.lower(), user=self.user)[0] 
                for tag_name in tags
            ]            
            self.tags.add(*tag_objects)

    class Meta:
        abstract = True
    
    def tags_for_user(self, user: User) -> list['Tag']:
        return list(self.tags.filter(user=user))


class NodeModel(EmbeddableModel, TaggableModel, PrivacySettingsModel, TimeStampedModel):
    source_links = GenericRelation('Link', content_type_field='source_content_type', object_id_field='source_object_id', related_query_name='source')
    target_links = GenericRelation('Link', content_type_field='target_content_type', object_id_field='target_object_id', related_query_name='target')

    class Meta:
        abstract = True

    def all_links(self, user: Optional[User] = None):
        content_type = ContentType.objects.get_for_model(self)
        user = self.user if user is None else user
        privacy_filter = Link.get_privacy_filter(user, 'fof')
        links = Link.objects.filter(
            models.Q(source_content_type=content_type, source_object_id=self.pk) |
            models.Q(target_content_type=content_type, target_object_id=self.pk)
        ).select_related('link_type')
        print(links.all())
        return links.filter(privacy_filter)

    def all_linked_objects(self, user: Optional[User] = None) -> list['NodeModel']:
        objects = []
        for link in self.all_links(user=user):
            if link.target_content_object == self:
                objects.append(link.source_content_object)
            else:
                objects.append(link.target_content_object)
        return objects

    def get_link_groups(self, user: Optional[User] = None) -> dict[tuple[LinkType, str], list['NodeModel']]:
        link_groups = defaultdict(list)
        for link in self.all_links(user):
            direction = "outgoing" if link.source_content_object == self else "incoming"
            key = (link.link_type, direction)
            target = link.target_content_object if direction == "outgoing" else link.source_content_object
            link_groups[key].append(target)
        return dict(link_groups)

    def related_nodes_filter(self, other_model_class: type['NodeModel']) -> Q:
        other_model_content_type = ContentType.objects.get_for_model(other_model_class)
        model_content_type = ContentType.objects.get_for_model(self)

        exclude_conditions = Q()

        exclude_conditions |= Q(source_links__source_content_type=other_model_content_type)
        exclude_conditions |= Q(target_links__target_content_type=other_model_content_type)

        if other_model_class == Link:
            exclude_conditions |= Q(source_content_type=model_content_type, source_object_id=self.pk)
            exclude_conditions |= Q(target_content_type=model_content_type, target_object_id=self.pk)
        
        if isinstance(self, other_model_class):
            exclude_conditions |= Q(pk=self.pk)
        
        return exclude_conditions    


class Link(NodeModel, PrivacySettingsModel):
    # Source generic foreign key fields
    source_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="source_links")
    source_object_id = models.PositiveIntegerField()
    source_content_object = GenericForeignKey('source_content_type', 'source_object_id')

    # Target generic foreign key fields
    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="target_links")
    target_object_id = models.PositiveIntegerField()
    target_content_object = GenericForeignKey('target_content_type', 'target_object_id')

    link_type = models.ForeignKey(LinkType, on_delete=models.CASCADE)


    class Meta:
        unique_together = ['source_content_type', 'source_object_id', 'target_content_type', 'target_object_id', 'link_type']
        ordering = ['link_type']

    def related_nodes_filter(self, other_model_class: type[NodeModel]) -> Q:
        exclude_conditions = super().related_nodes_filter(other_model_class)
        if isinstance(self.source_content_object, other_model_class):
            exclude_conditions |= Q(pk=self.source_object_id)
        if isinstance(self.target_content_object, other_model_class):
            exclude_conditions |= Q(pk=self.target_object_id)
        return exclude_conditions

    @classmethod
    def get_list_url(cls):
        return reverse('links')

    def get_absolute_url(self):
        return reverse('link_view', args=[self.pk])

    def is_viewable_by(self, user: User, privacy_level: str = 'fof') -> bool:
        return self.source_content_object.is_viewable_by(user, privacy_level) and self.target_content_object.is_viewable_by(user, privacy_level) # type: ignore

    @classmethod
    def get_privacy_filter(cls, user: User, privacy_level: str = 'fof') -> Q:
        """
        Returns a QuerySet of Link objects that are viewable by the specified user.
        A Link is viewable if both its source and target nodes are viewable by the user.
        """

        # Get content types for all NodeModels
        node_content_types = ContentType.objects.filter(app_label='app', model__in=['memo', 'reference', 'inkling'])

        # Generate Q objects for each content type based on viewability
        combined_filters = Q()
        for content_type in node_content_types:
            node_model = content_type.model_class()
            if issubclass(node_model, PrivacySettingsModel): # type: ignore
                model_filter = node_model.get_privacy_filter(user, privacy_level)
                combined_filters |= Q(source_content_type=content_type, source_object_id__in=node_model.objects.filter(model_filter)) & \
                                    Q(target_content_type=content_type, target_object_id__in=node_model.objects.filter(model_filter))
        
        return combined_filters




class Memo(TitleAndContentModel, NodeModel, SummarizableModel, PrivacySettingsModel):
    class Meta:
        ordering = ['-created_at']

    @classmethod
    def get_list_url(cls):
        return reverse('memos')

    def get_absolute_url(self):
        return reverse('memo_view', args=[str(self.pk)])


class Reference(TitleAndContentModel, NodeModel, SummarizableModel, PrivacySettingsModel):
    source_url = models.URLField(max_length=2000, blank=True, null=True)
    source_name = models.CharField(max_length=255, blank=True, null=True)
    publication_date = models.DateField(blank=True, null=True)
    authors = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']

    def get_absolute_url(self):
        return reverse('reference_view', args=[str(self.pk)])

    @classmethod
    def get_list_url(cls):
        return reverse('references')


class Inkling(TitleAndContentModel, NodeModel, PrivacySettingsModel):
    class Meta:
        ordering = ['-created_at']
    
    def get_absolute_url(self):
        return reverse('inkling_view', args=[str(self.pk)])

    @classmethod
    def get_list_url(cls):
        return reverse('inklings')


class Tag(EmbeddableModel, UserOwnedModel, TimeStampedModel):
    name = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        self.name = self.name.lower().strip()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['user', 'name']
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def title(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tag_view', args=[str(self.pk)])
    
    @classmethod
    def get_list_url(cls):
        return reverse('tags')


@dataclass
class Query:
    query: str
    embedding: np.ndarray


class UserInvite(TimeStampedModel):
    # Status Choices
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
    ]

    # Fields
    inviter = models.ForeignKey(User, related_name='sent_invites', on_delete=models.CASCADE)
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)  # Generates a unique UUID for every invite
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)

    def __str__(self):
        return f"Invite for {self.email} by {self.inviter.username}"

    class Meta:
        unique_together = ['inviter', 'email']
        pass

    def get_absolute_url(self):
        return reverse('invite_view', args=[str(self.pk)])
    
    @property
    def link(self):
        # returns the full url with the token, including https://sitename.com
        return reverse('signup') + f'?invite_token={self.token}'