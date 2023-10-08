from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView, View)

from app.mixins import (GenerateTitleAndTagsMixin, SimilarObjectMixin,
                        UserScopedMixin)
from app.models import Reference


class EditReferenceView(UpdateView, LoginRequiredMixin, UserScopedMixin, GenerateTitleAndTagsMixin):
    model = Reference
    fields = ['title', 'content']
    template_name = 'reference/edit.html'


class DeleteReferenceView(SimilarObjectMixin, DeleteView, UserScopedMixin):
    model = Reference
    success_url = '/'
        
    def get_success_url(self):
        """
        Redirect to the most similar tag after deletion.
        """
        similar_object = self.get_similar_object()
        if not similar_object:
            return reverse('home')
        return reverse('view_reference', args=[similar_object.pk])
