from django import forms
from martor.fields import MartorFormField

from .models import ContentType, Inkling, Link, LinkType, Memo, Reference, Tag


class SearchForm(forms.Form):
    query = forms.CharField(
        max_length=255, 
        widget=forms.TextInput(attrs={'placeholder': 'Search...'})
    )


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']


class MemoForm(forms.ModelForm):
    content = MartorFormField()

    class Meta:
        model = Memo
        fields = ['title', 'content']


class LinkForm(forms.ModelForm):
    link_type = forms.CharField(max_length=100)

    class Meta:
        model = Link
        fields = ['source_content_type', 'source_object_id', 'target_content_type', 'target_object_id', 'link_type']

    def clean(self):
        cleaned_data = super().clean()
        link_type_id: str = cleaned_data.get('link_type') # type: ignore
        if link_type_id.endswith('_reverse'):
            cleaned_data['source_object_id'], cleaned_data['target_object_id'] = cleaned_data['target_object_id'], cleaned_data['source_object_id']
            cleaned_data['source_content_type'], cleaned_data['target_content_type'] = cleaned_data['target_content_type'], cleaned_data['source_content_type']
            cleaned_data['link_type'] = link_type_id.removesuffix('_reverse')
        cleaned_data['link_type'] = LinkType.objects.get(pk=int(link_type_id))
        return cleaned_data


class LinkTypeForm(forms.ModelForm):
    class Meta:
        model = LinkType
        fields = ['name', 'reverse_name']


class InklingForm(forms.ModelForm):
    title = forms.CharField(required=False)

    class Meta:
        model = Inkling
        fields = ['title', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }