from typing import Any

import requests
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


class AddTagForm(forms.Form):
    TAGGABLE_CLASSES = {
        "memo": Memo,
        "reference": Reference,
        "inkling": Inkling,
    }

    tag_id = forms.IntegerField(widget=forms.HiddenInput())
    target_class_name = forms.ChoiceField(choices=[(k, k) for k in TAGGABLE_CLASSES.keys()], widget=forms.HiddenInput())
    target_id = forms.IntegerField(widget=forms.HiddenInput())

    def clean_target_class_name(self):
        target_class_name = self.cleaned_data['target_class_name']
        return self.TAGGABLE_CLASSES[target_class_name]

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
        cleaned_data['link_type'] = LinkType.objects.get(pk=int(cleaned_data['link_type']))
        return cleaned_data


class URLReferenceForm(forms.Form):
    url = forms.URLField(
        max_length=1000, 
        widget=forms.URLInput(attrs={'placeholder': 'https://www.example.com'}),
        help_text="Enter a valid and accessible webpage URL.",
        error_messages={
            'invalid': "Please enter a valid URL.",
        }
    )

    # def clean_url(self):
    #     url = self.cleaned_data.get('url')
        
    #     try:
    #         response = requests.head(url, timeout=20)  # Using a HEAD request for faster validation
    #         if response.status_code != 200:
    #             raise forms.ValidationError("The provided URL is not accessible.")
    #     except requests.RequestException:
    #         raise forms.ValidationError("Failed to validate the URL. Ensure it's correct and accessible.")

    #     return url


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