
from django.db.models import F

from app.embeddings import generate_embedding
from app.prompting import get_tags_and_title

from .models import NodeModel


class GenerateTitleAndTagsMixin:
    def form_valid(self, form):
        object = form.save(commit=False)
        if not isinstance(object, NodeModel):
            return super().form_valid(self, form) # type: ignore
        title = None if object.title == "Untitled" else object.title
        if (not title) or (not object.tags.exists()):
            user_tags = self.request.user.tag_set.all() # type: ignore
            ai_content = get_tags_and_title(object.content, title, user_tags)
            object.create_tags(ai_content['tags'])

            if not title:
                title = ai_content.get('title')
            if title:
                object.title = title

        object.embedding = generate_embedding(f'{object.title}: {object.content}')
        object.save()  # Save to the database
        return redirect(self.success_url) # type: ignore


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
        return self.model.objects.filter(user=self.request.user).annotate(distance=F('embedding').distance(embedding)).order_by('distance').exclude(pk=object.pk).first()  # type: ignore