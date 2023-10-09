import django_tables2 as tables
from django.middleware.csrf import get_token
from django.urls import reverse
from django.utils.html import format_html, mark_safe  # type: ignore

from .models import Inkling, LinkType, Memo, NodeModel, Reference


def delete_action_html(record, csrf_token):
    delete_url = reverse(f'delete_{record._meta.model_name}', args=[record.pk])
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
    edit_url = reverse(f'edit_{record._meta.model_name}', args=[record.pk])
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
        template_name = "django_tables2/bootstrap4.html"
        fields = ("title", "content", "created_at", "updated_at", "actions")

    def render_title(self, record):
        url = reverse(f'view_{record._meta.model_name}', args=[record.pk])
        return mark_safe(f'<a href="{url}">{record.title}</a>')

    def render_tags(self, value):
        return ", ".join(str(tag) for tag in value.all())

    def render_links(self, record):
        return ", ".join(str(link) for link in record.all_links())
    
    def render_actions(self, record):
        csrf_token = get_token(self.context['request']) # type: ignore
        return delete_action_html(record, csrf_token)



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
