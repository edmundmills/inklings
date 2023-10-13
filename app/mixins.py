
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy

from app.embeddings import generate_embedding
from app.prompting import ChatGPT, Completer, get_generated_metadata

from .models import (EmbeddableModel, NodeModel, PrivacySettingsModel,
                     SummarizableModel, TaggableModel, TitleAndContentModel,
                     UserOwnedModel)


def add_metadata(object: UserOwnedModel, completer: Completer):
    if not isinstance(object, TaggableModel) and not isinstance(object, TitleAndContentModel) and not isinstance(object, SummarizableModel):
        return object
    title = None if object.title == "Untitled" else object.title # type: ignore
    user_tags = object.user.tag_set.all() # type: ignore
    ai_content = get_generated_metadata(completer, object.content, title, user_tags) # type: ignore
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
        object.embedding = generate_embedding(object.content, object.title) # type: ignore
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
        # if this request came from an object's detail view and deleted the object, redirect to the list view page for the object class
        if self.request.META.get('HTTP_REFERER', '').startswith(self.request.build_absolute_uri(self.object.get_absolute_url())): # type: ignore
            return self.model.get_list_url() # type: ignore
        # otherwise redirect back
        return self.request.META.get('HTTP_REFERER', reverse_lazy('/')) # type: ignore


class UserScopedMixin:
    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user) # type: ignore


class PrivacyScopedMixin:
    def get_queryset(self):
        if issubclass(self.model, PrivacySettingsModel): # type: ignore
            filter = self.model.get_privacy_filter(self.request.user, 'fof') # type: ignore
        else:
            filter = Q(user=self.request.user) # type: ignore
        return self.model.objects.filter(filter) # type: ignore


class LinkedContentMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) # type: ignore
        if isinstance(self.object, NodeModel): # type: ignore
            context['linked_content'] = self.object.get_link_groups(self.request.user) # type: ignore
        return context
    
