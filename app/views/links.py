from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import CreateView, DeleteView

from app.forms import LinkForm
from app.mixins import RedirectBackMixin, SimilarObjectMixin, UserScopedMixin
from app.models import Link


class CreateLinkView(LoginRequiredMixin, CreateView, RedirectBackMixin):
    form_class = LinkForm
    template_name = 'path_to_link_create_template.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        self.object = form.save()
        # messages.success(self.request, "Link created successfully!")
        return redirect(self.get_success_url())


class DeleteLinkView(DeleteView, UserScopedMixin, RedirectBackMixin, LoginRequiredMixin):
    model = Link
    success_url = '/'
