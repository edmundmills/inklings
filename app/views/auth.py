from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import (CreateView, DetailView, ListView, UpdateView,
                                  View)

from app.mixins import UserScopedMixin
from app.models import Memo


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'auth/signup.html', {'form': form})


class HomeView(ListView, LoginRequiredMixin, UserScopedMixin):
    model = Memo
    template_name = 'layouts/home.html'
    
    def get_queryset(self):
        return Memo.objects.filter(user=self.request.user).order_by('-created_at')

    def dispatch(self, request, *args, **kwargs):
        memos = Memo.objects.filter(user=self.request.user).order_by('-updated_at') 
        if memos.exists():
            return redirect('memo_view', memos[0].pk)
        return super().dispatch(request, *args, **kwargs)


