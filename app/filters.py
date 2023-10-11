import django_filters
from django.db import models

from .models import Inkling, Link, LinkType, Memo, Reference, Tag


class BaseNodeFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', label='Search')

    class Meta:
        model = Reference  # Placeholder
        fields = []

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(content__icontains=value)
        )

class ReferenceFilter(BaseNodeFilter):
    class Meta(BaseNodeFilter.Meta):
        model = Reference
        fields = BaseNodeFilter.Meta.fields + ['source_url', 'source_name']

class InklingFilter(BaseNodeFilter):
    class Meta(BaseNodeFilter.Meta):
        model = Inkling

class MemoFilter(BaseNodeFilter):
    class Meta(BaseNodeFilter.Meta):
        model = Memo

class LinkTypeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    reverse_name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = LinkType
        fields = ['name', 'reverse_name']


class LinkFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', label='Search')

    class Meta:
        model = Link
        fields = []

    def filter_search(self, queryset, name, value):
        # Split value to search for link_type name and object name separately
        lookups = (
            models.Q(link_type__name__icontains=value) |
            models.Q(link_type__reverse_name__icontains=value) |
            models.Q(source_content_object__title__icontains=value) |
            models.Q(target_content_object__title__icontains=value)
        )
        return queryset.filter(lookups)
    
class TagFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Tag
        fields = ['name']
