from django import forms
from django.db.models import QuerySet

from .helpers import create_tags
from .models import Inkling, Memo


class CommaSeparatedTagsField(forms.CharField):
    def to_python(self, value):
        if not value:
            return []
        return [tag.strip() for tag in value.split(',')]

    def prepare_value(self, value):
        if isinstance(value, list):
            return ', '.join([str(tag) for tag in value])
        elif isinstance(value, QuerySet):
            return ', '.join([str(tag) for tag in value])
        return super().prepare_value(value)

class CommaSeparatedInput(forms.TextInput):
    template_name = 'forms/input_comma_separated.html'



class MemoForm(forms.ModelForm):
    class Meta:
        model = Memo
        fields = ['title', 'content', 'tags']
    
    tags = CommaSeparatedTagsField(widget=CommaSeparatedInput(attrs={'class': 'form-control'}), required=False)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            instance.tags.clear()
            tag_names = [name.strip() for name in self.cleaned_data['tags']]
            create_tags(tag_names, instance)
        return instance

class InklingForm(forms.ModelForm):
    tags = CommaSeparatedTagsField(widget=CommaSeparatedInput(attrs={'class': 'form-control'}), required=False)

    class Meta:
        model = Inkling
        fields = ['content', 'tags']

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            instance.tags.clear()
            print(self.cleaned_data['tags'])
            tag_names = [name.strip() for name in self.cleaned_data['tags']]
            create_tags(tag_names, instance)
        return instance


class BaseInklingFormSet(forms.BaseInlineFormSet):
    def clean(self):
        """Check that no two inklings have the same title and content."""
        super().clean()

        for form in self.forms:
            # Skip forms marked for deletion
            if self.can_delete and self._should_delete_form(form):  # type: ignore
                print('skip')
                continue
            
            # Assuming 'title' and 'content' are fields in your Inkling model
            title = form.cleaned_data.get('title')
            content = form.cleaned_data.get('content')
            title = form.cleaned_data.get('title')
            content = form.cleaned_data.get('content')
            tags = form.cleaned_data.get('tags')

            if not title and not content and not tags:
                # remove the form from self.forms if it's empty
                self.forms.remove(form)


InklingFormset = forms.inlineformset_factory(
    Memo, 
    Inkling,
    form=InklingForm,
    formset=BaseInklingFormSet,  # specify the custom formset class here
    fields=('content', 'tags'), 
    extra=1,
    can_delete=True
)
