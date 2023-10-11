from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView, View)

from app.fetch_reference import create_reference_from_url
from app.forms import URLReferenceForm
from app.mixins import (GenerateTitleAndTagsMixin, RedirectBackMixin,
                        UserScopedMixin, add_metadata)
from app.models import Reference
from app.prompting import ChatGPT


class ReferenceCreateView(LoginRequiredMixin, CreateView):
    model = Reference
    form_class = URLReferenceForm
    completer = ChatGPT()

    def form_invalid(self, form):
        print(form.errors)
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER', reverse_lazy('/')))

    def form_valid(self, form):
        url = form.cleaned_data['url']
        self.object = create_reference_from_url(url, ChatGPT(), self.request.user)
        self.object = add_metadata(self.object, self.completer)
        return HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance', None)
        return kwargs

    def get_success_url(self):
        return reverse('reference_view', args=[self.object.pk])


class EditReferenceView(LoginRequiredMixin, UserScopedMixin, GenerateTitleAndTagsMixin, UpdateView):
    model = Reference
    fields = ['title', 'content']
    template_name = 'reference/edit.html'


class DeleteReferenceView(RedirectBackMixin, UserScopedMixin, LoginRequiredMixin, DeleteView):
    model = Reference
    success_url = '/'