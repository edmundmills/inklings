from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView

from app.embeddings import (generate_embedding, get_similar_nodes,
                            get_similar_tags, sort_by_distance)
from app.mixins import LinkedContentMixin, UserScopedMixin
from app.models import Inkling, Memo, Query, Reference, Tag


class FeedContentMixin(LinkedContentMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feed_objects = []
        object = self.object # type: ignore
        user = self.request.user # type: ignore
        for search_class in [Reference, Inkling, Memo]:
            similar_nodes = get_similar_nodes(object, search_class, user, 10)
            feed_objects.extend(similar_nodes)

        feed_objects = sort_by_distance(object.embedding, feed_objects)
        context['feed_objects'] = feed_objects
        context['related_tags'] = get_similar_tags(object, user, 10)
        return context



class FeedView(LoginRequiredMixin, UserScopedMixin, FeedContentMixin, DetailView):
    pass


class TagFeedView(FeedView):
    model = Tag
    template_name = 'feed/feed_tag.html'


class MemoFeedView(FeedView):
    model = Memo
    template_name = 'feed/feed_memo.html'


class InklingFeedView(FeedView):
    model = Inkling
    template_name = 'feed/feed_inkling.html'


class ReferenceFeedView(FeedView):
    model = Reference
    template_name = 'feed/feed_reference.html'


class QueryFeedView(FeedView):
    model = Query # type: ignore
    template_name = 'feed/feed_query.html'

    def get_object(self, queryset=None):
        query = self.request.GET.get('query')
        embedding = generate_embedding(query)
        return Query(query, embedding) # type: ignore
