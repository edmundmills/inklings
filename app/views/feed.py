from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from django.views.generic import DetailView

from app.embeddings import (generate_embedding, get_similar_nodes,
                            get_similar_tags, sort_by_distance)
from app.forms import InklingForm
from app.mixins import LinkedContentMixin, PrivacyScopedMixin, UserScopedMixin
from app.models import Inkling, Link, Memo, Query, Reference, Tag


class FeedContentMixin(LinkedContentMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object = self.object # type: ignore
        user = self.request.user # type: ignore
        context['current_user'] = user
        context['hatch_inkling_form'] = InklingForm()
        context['similar_tags'] = get_similar_tags(object, user, 10)
        for privacy_level in ['own', 'friends', 'fof']:
            feed_objects = []
            for search_class in [Reference, Inkling, Memo]:
                similar_nodes = get_similar_nodes(object, search_class, user, 10, privacy_level=privacy_level)
                feed_objects.extend(similar_nodes)
            feed_objects = sort_by_distance(object.embedding, feed_objects)
            context[f'feed_objects_{privacy_level}'] = feed_objects
        return context



class FeedView(LoginRequiredMixin, PrivacyScopedMixin, FeedContentMixin, DetailView):
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


class LinkFeedView(FeedView):
    model = Link # type: ignore
    template_name = 'feed/feed_link.html'


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
    user = request.user
    context['current_user'] = user
    for privacy_level in ['own', 'friends', 'fof']:
        feed_objects = []

        for search_class in [Memo, Reference, Link, Inkling]:
            recent = search_class.objects.filter(search_class.get_privacy_filter(user, privacy_level)).order_by('-updated_at')[:20]
            feed_objects.extend(recent)

        feed_objects = sorted(feed_objects, key=lambda x: x.updated_at, reverse=True)

        if user.intention_embedding is not None:
            sorted_feed_objects = []
            subsort_size = 10
            for i in range(0, len(feed_objects), subsort_size):
                sorted_feed_objects.extend(sort_by_distance(user.intention_embedding, feed_objects[i:i+subsort_size]))
            feed_objects = sorted_feed_objects
        
        context[f'feed_objects_{privacy_level}'] = feed_objects
    return render(request, 'feed/feed_new.html', context=context)