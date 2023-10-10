
from django.shortcuts import redirect
from django.urls import reverse_lazy
from pgvector.django import CosineDistance

from app.embeddings import generate_embedding
from app.prompting import ChatGPT, Completer, get_generated_metadata

from .models import (EmbeddableModel, NodeModel, SummarizableModel,
                     TaggableModel, TitleAndContentModel, UserOwnedModel)


def add_metadata(object: UserOwnedModel, completer: Completer):
    if not isinstance(object, TaggableModel) and not isinstance(object, TitleAndContentModel) and not isinstance(object, SummarizableModel):
        return object
    title = None if object.title == "Untitled" else object.title
    user_tags = object.user.tag_set.all() # type: ignore
    ai_content = get_generated_metadata(completer, object.content, title, user_tags)
    print(ai_content)
    if isinstance(object, TitleAndContentModel) and not title:
        new_title = ai_content.get('title')
        if not new_title:
            new_title = 'Untitled'
        object.title = new_title
    if isinstance(object, SummarizableModel):
        summary = ai_content.get('summary')
        if summary:
            object.summary = summary
    if isinstance(object, EmbeddableModel):
        object.embedding = generate_embedding(object.content, object.title)
    object.save()
    if isinstance(object, TaggableModel):
        tags = ai_content.get('tags', list())
        object.create_tags(tags)
    return object


class GenerateTitleAndTagsMixin:
    completer = ChatGPT()

    def form_valid(self, form):
        object = form.save(commit=False)
        object.user = self.request.user # type: ignore
        object = add_metadata(object, self.completer)
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

