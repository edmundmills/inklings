from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from django.views.generic import DetailView

from app.embeddings import (generate_embedding, get_similar_nodes,
                            get_similar_tags, sort_by_distance)
from app.mixins import LinkedContentMixin, UserScopedMixin
from app.models import Inkling, Link, Memo, Query, Reference, Tag, UserProfile


class FeedContentMixin(LinkedContentMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feed_objects = []
        object = self.object # type: ignore
        user = self.request.user # type: ignore
        for search_class in [Reference, Inkling, Memo]:
            similar_nodes = get_similar_nodes(object, search_class, user, 10)
            feed_objects.extend(similar_nodes)
        context['similar_tags'] = get_similar_tags(object, user, 10)
        feed_objects += context['similar_tags']
        feed_objects = sort_by_distance(object.embedding, feed_objects)
        context['feed_objects'] = feed_objects
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

@login_required
def new_feed_view(request):
    context = dict()
    feed_objects = []
    user = request.user
    user_profile = UserProfile.objects.get(user=user)

    for search_class in [Tag, Memo, Reference, Link, Inkling]:
        feed_objects.extend(search_class.objects.filter(user=user).order_by('-updated_at')[:20])

    feed_objects = sorted(feed_objects, key=lambda x: x.updated_at, reverse=True)

    if user_profile.intention:
        embedding = generate_embedding(user_profile.intention)
        sorted_feed_objects = []
        subsort_size = 10
        for i in range(0, len(feed_objects), subsort_size):
            sorted_feed_objects.extend(sort_by_distance(embedding, feed_objects[i:i+subsort_size]))
        feed_objects = sorted_feed_objects
    
    context['feed_objects'] = feed_objects
    return render(request, 'feed/feed_new.html', context=context)