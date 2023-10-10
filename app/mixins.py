
from django.shortcuts import redirect
from django.urls import reverse_lazy
from pgvector.django import CosineDistance

from app.embeddings import generate_embedding
from app.prompting import ChatGPT, get_tags_and_title

from .models import (EmbeddableModel, NodeModel, TaggableModel,
                     TitleAndContentModel)


class GenerateTitleAndTagsMixin:
    completer = ChatGPT()

    def form_valid(self, form):
        object = form.save(commit=False)
        object.user = self.request.user # type: ignore
        if not isinstance(object, TaggableModel) or not isinstance(object, TitleAndContentModel):
            return super().form_valid(self, form) # type: ignore
        title = None if object.title == "Untitled" else object.title
        if (not title) or (not object.tags.exists()):
            user_tags = self.request.user.tag_set.all() # type: ignore
            ai_content = get_tags_and_title(self.completer, object.content, title, user_tags)
            if not title:
                title = ai_content.get('title')
            if title:
                object.title = title
            tags = ai_content['tags']
        else:
            tags = []
        if isinstance(object, EmbeddableModel):
            object.embedding = generate_embedding(object.content, object.title)
        object.save()  # Save to the database
        object.create_tags(tags)
        self.object = object
        return redirect(self.get_success_url()) # type: ignore


class RedirectBackMixin:
    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER', reverse_lazy('/')) # type: ignore


class UserScopedMixin:
    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user) # type: ignore


class LinkedContentMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) # type: ignore
        if isinstance(self.object, NodeModel): # type: ignore
            context['linked_content'] = self.object.get_link_groups() # type: ignore
        return context
    

class SimilarObjectMixin:    
    def get_similar_object(self):
        """
        Returns the most similar object based on the embedding.
        """
        object = self.get_object() # type: ignore
        if not isinstance(object, NodeModel):
            return None
        embedding = object.embedding
        return self.model.objects.filter(user=self.request.user).alias(distance=CosineDistance('embedding', embedding)).exclude(pk=object.pk).filter(distance__lt=0.5).order_by('distance').first() # type: ignore

