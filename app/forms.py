from django import forms

from .models import Inkling, Memo, Tag


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']

class MemoForm(forms.ModelForm):
    class Meta:
        model = Memo
        fields = ['title', 'content', 'tags']

InklingFormset = forms.inlineformset_factory(
    Memo, 
    Inkling, 
    fields=('title', 'content', 'tags'), 
    extra=1,
    can_delete=True
)
