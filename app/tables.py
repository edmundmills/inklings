import django_tables2 as tables
from django.urls import reverse
from django.utils.html import mark_safe

from .models import Inkling, LinkType, Memo, NodeModel, Reference


class BaseNodeTable(tables.Table):
    tags = tables.Column(empty_values=(), orderable=False)
    links = tables.Column(empty_values=(), orderable=False)
    
    class Meta:
        model = NodeModel
        template_name = "django_tables2/bootstrap4.html"
        fields = ("title", "content", "created_at", "updated_at")

    def render_title(self, record):
        url = reverse(f'view_{record._meta.model_name}', args=[record.pk])
        return mark_safe(f'<a href="{url}">{record.title}</a>')

    def render_tags(self, value):
        return ", ".join(str(tag) for tag in value.all())

    def render_links(self, record):
        return ", ".join(str(link) for link in record.all_links())

class ReferenceTable(BaseNodeTable):
    class Meta(BaseNodeTable.Meta):
        model = Reference
        fields = BaseNodeTable.Meta.fields + ("source_url", "source_name", "publication_date", "authors")

class InklingTable(BaseNodeTable):
    class Meta(BaseNodeTable.Meta):
        model = Inkling

class MemoTable(BaseNodeTable):
    class Meta(BaseNodeTable.Meta):
        model = Memo

class LinkTypeTable(tables.Table):
    class Meta:
        model = LinkType
        template_name = "django_tables2/bootstrap4.html"
        fields = ("name", "reverse_name", "created_at", "updated_at")
