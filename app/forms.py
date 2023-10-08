from django import forms
from martor.fields import MartorFormField

from .models import Inkling, LinkType, Memo, Tag


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


class LinkTypeForm(forms.ModelForm):
    class Meta:
        model = LinkType
        fields = ['name', 'reverse_name']


class InklingForm(forms.ModelForm):
    class Meta:
        model = Inkling
        fields = ['title', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }