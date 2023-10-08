from django import forms
from martor.fields import MartorFormField

from .models import ContentType, Inkling, Link, LinkType, Memo, Tag


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
    source_inkling_id = forms.IntegerField()
    target_inkling_id = forms.IntegerField()
    linkType = forms.CharField(max_length=100)  # This should match the POST field name

    class Meta:
        model = Link
        fields = []

    def clean(self):
        cleaned_data = super().clean()
        link_type_id = cleaned_data.get('linkType')
        if link_type_id and link_type_id.endswith('_reverse'):
            cleaned_data['source_inkling_id'], cleaned_data['target_inkling_id'] = cleaned_data['target_inkling_id'], cleaned_data['source_inkling_id']
            cleaned_data['linkType'] = link_type_id.removesuffix('_reverse')
        return cleaned_data

    def save(self, *args, **kwargs):
        instance = super().save(commit=False)
        instance.source_content_type = ContentType.objects.get_for_model(Inkling)
        instance.source_object_id = self.cleaned_data['source_inkling_id']
        instance.target_content_type = ContentType.objects.get_for_model(Inkling)
        instance.target_object_id = self.cleaned_data['target_inkling_id']
        instance.link_type = LinkType.objects.get(pk=self.cleaned_data['linkType'])
        instance.save()
        return instance


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