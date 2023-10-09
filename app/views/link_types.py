from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.forms import LinkTypeForm
from app.mixins import RedirectBackMixin, UserScopedMixin
from app.models import LinkType


class CreateLinkTypeView(LoginRequiredMixin, CreateView, RedirectBackMixin):
    model = LinkType
    form_class = LinkTypeForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        self.object = form.save()
        return redirect(self.get_success_url())


class EditLinkTypeView(LoginRequiredMixin, UpdateView, UserScopedMixin, RedirectBackMixin):
    model = LinkType
    form_class = LinkTypeForm
    template_name = 'link_type/edit.html'
    context_object_name = 'link_type'


class DeleteLinkTypeView(LoginRequiredMixin, DeleteView, UserScopedMixin, RedirectBackMixin):
    model = LinkType
    context_object_name = 'link_type'

