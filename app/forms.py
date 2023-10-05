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
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }



class BaseInklingFormSet(forms.BaseInlineFormSet):
    def clean(self):
        """Check that no two inklings have the same title and content."""
        super().clean()

        for form in self.forms:
            # Skip forms marked for deletion
            if self.can_delete and self._should_delete_form(form):  # type: ignore
                print('skip')
                continue

            content = form.cleaned_data.get('content')
            if not content:
                # remove the form from self.forms if it's empty
                self.forms.remove(form)


InklingFormset = forms.inlineformset_factory(
    Memo, 
    Inkling,
    form=InklingForm,
    formset=BaseInklingFormSet,  # specify the custom formset class here
)
