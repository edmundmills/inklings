from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView

from app.embeddings import generate_embedding
from app.mixins import LinkedContentMixin, UserScopedMixin
from app.models import Inkling, Memo, Query, Reference, Tag


class FeedView(LoginRequiredMixin, UserScopedMixin, LinkedContentMixin, DetailView):
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
