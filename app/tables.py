import django_tables2 as tables
from django.middleware.csrf import get_token
from django.urls import reverse
from django.utils.html import format_html, mark_safe  # type: ignore

from .models import Inkling, Link, LinkType, Memo, NodeModel, Reference

TEMPLATE_NAME = "django_tables2/bootstrap5.html"

def link_to_object_html(record):
    url = reverse(f'{record._meta.model_name}_view', args=[record.pk])
    return mark_safe(f'<a href="{url}">{record.title}</a>')

def delete_action_html(record, csrf_token):
    delete_url = reverse(f'{record._meta.model_name}_delete', args=[record.pk])
    return format_html(
        '''<form method="post" action="{}" onsubmit="return confirm('Are you sure you want to delete this {}?');">
            <input type="hidden" name="csrfmiddlewaretoken" value="{}">
            <button type="submit" class="btn btn-sm" name="Delete">Delete</button>
            </form>''',
        delete_url,
        record.__class__.__name__,
        csrf_token
    )

def edit_action_html(record):
    edit_url = reverse(f'{record._meta.model_name}_edit', args=[record.pk])
    return format_html(
        '<a href="{}">Edit</a>',
        edit_url,
    )

class BaseNodeTable(tables.Table):
    tags = tables.Column(empty_values=(), orderable=False)
    links = tables.Column(empty_values=(), orderable=False)
    actions = tables.Column(empty_values=(), orderable=False, verbose_name='Actions')

    class Meta:
        model = NodeModel
        template_name = TEMPLATE_NAME
        fields = ("title", "tags", "links")

    def render_title(self, record):
        return link_to_object_html(record)

    def render_tags(self, value):
        return mark_safe(", ".join(link_to_object_html(tag) for tag in value.all()))

    def render_links(self, record):
        return mark_safe(", ".join(link_to_object_html(other) for other in record.all_linked_objects()))
    
    def render_actions(self, record):
        csrf_token = get_token(self.context['request']) # type: ignore
        return delete_action_html(record, csrf_token)



class ReferenceTable(BaseNodeTable):
    class Meta(BaseNodeTable.Meta):
        model = Reference
        fields = ("title", "summary", "source_url", "source_name", "publication_date", "authors", "created_at", "updated_at", "actions")

class InklingTable(BaseNodeTable):
    class Meta(BaseNodeTable.Meta):
        model = Inkling
        fields = ("title", "content", "created_at", "updated_at", "actions")

class MemoTable(BaseNodeTable):
    class Meta(BaseNodeTable.Meta):
        model = Memo
        fields = ("title", "summary", "created_at", "updated_at", "actions")

class LinkTypeTable(tables.Table):
    class Meta:
        model = LinkType
        template_name = TEMPLATE_NAME
        fields = ("name", "reverse_name", "created_at", "updated_at")

class LinkTable(tables.Table):
    class Meta:
        model = Link
        template_name = TEMPLATE_NAME
        fields = ("source", "link_type", "target", "created_at", "updated_at")

    def render_source(self, record):
        return link_to_object_html(record.source_content_object)

    def render_target(self, record):
        return link_to_object_html(record.target_content_object)

    def render_link_type(self, record):
        return record.link_type.name
