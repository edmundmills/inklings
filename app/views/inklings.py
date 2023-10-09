from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView, View)

from app.forms import InklingForm
from app.mixins import (GenerateTitleAndTagsMixin, SimilarObjectMixin,
                        UserScopedMixin)
from app.models import Inkling


class CreateInklingView(LoginRequiredMixin, GenerateTitleAndTagsMixin, CreateView):
    model = Inkling
    form_class = InklingForm
    
    def get_success_url(self):
        return reverse('view_inkling', args=[self.object.pk])


class DeleteInklingView(SimilarObjectMixin, UserScopedMixin, DeleteView):
    model = Inkling

    def get_success_url(self):
        """
        Redirect to the most similar object after deletion.
        """
        similar_object = self.get_similar_object()
        if not similar_object:
            return reverse('home')
        return reverse('view_inkling', args=[similar_object.pk])
