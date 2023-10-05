from django import template
from django.forms import BoundField

register = template.Library()

@register.filter(name='as_bootstrap')
def as_bootstrap(field: BoundField) -> BoundField:
    """
    Render a Django form field with Bootstrap 4 classes.
    """
    # Add the Bootstrap class to the widget of the form field
    field.field.widget.attrs.update({'class': 'form-control'})
    return field

