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

from app.forms import InklingForm, LinkForm
from app.mixins import (GenerateTitleAndTagsMixin, RedirectBackMixin,
                        UserScopedMixin, add_metadata)
from app.models import ContentType, Inkling, Link
from app.prompting import ChatGPT


class CreateInklingView(LoginRequiredMixin, GenerateTitleAndTagsMixin, CreateView):
    model = Inkling
    form_class = InklingForm
    
    def get_success_url(self):
        return reverse('inkling_view', args=[self.object.pk])


class EditInklingView(UserScopedMixin, LoginRequiredMixin, UpdateView):
    model = Inkling
    form_class = InklingForm


class DeleteInklingView(LoginRequiredMixin, RedirectBackMixin, UserScopedMixin, DeleteView):
    model = Inkling


@login_required
def create_inkling_and_link(request):
    if not request.method == "POST":
        return redirect('/')
    inkling_form = InklingForm(request.POST)
    link_form = LinkForm(request.POST)
    if not (inkling_form.is_valid() and link_form.is_valid()):
        return redirect('/')
    inkling_instance = inkling_form.save(commit=False)
    inkling_instance.user = request.user 
    inkling_instance.save()
    link_instance = link_form.save(commit=False)
    link_instance.source_content_type = ContentType.objects.get_for_model(Inkling)
    link_instance.source_object_id = inkling_instance.id
    link_instance.user = request.user
    link_instance.save()
    add_metadata(inkling_instance, ChatGPT())
    return redirect(reverse('inkling_view', args=[inkling_instance.pk]))
