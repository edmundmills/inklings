from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DeleteView

from app.forms import LinkForm
from app.mixins import RedirectBackMixin, UserScopedMixin
from app.models import Link


class CreateLinkView(LoginRequiredMixin, RedirectBackMixin, CreateView):
    form_class = LinkForm
    template_name = '/'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)



class DeleteLinkView(DeleteView, UserScopedMixin, RedirectBackMixin, LoginRequiredMixin):
    model = Link
    success_url = '/'
