from django import template
from django.contrib.contenttypes.models import ContentType
from django.forms import BoundField

register = template.Library()

@register.filter(name='as_bootstrap')
def as_bootstrap(field: BoundField) -> BoundField:
    """
    Render a Django form field with Bootstrap classes.
    """
    # Add the Bootstrap class to the widget of the form field
    field.field.widget.attrs.update({'class': 'form-control'})
    return field


@register.filter(name='class_name')
def class_name(value):
    return value.__class__.__name__.lower()

@register.filter(name='content_type_id')
def content_type_id(value):
    return ContentType.objects.get_for_model(value).id
