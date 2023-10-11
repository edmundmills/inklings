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

from app.config import DEFAULT_LINK_TYPES, DEFAULT_TAGS
from app.mixins import UserScopedMixin
from app.models import LinkType, Memo, Tag, UserProfile
from app.prompting import ChatGPT, create_initial_data


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('get_intention')
    else:
        form = UserCreationForm()
    return render(request, 'auth/signup.html', {'form': form})

@login_required
def get_intention(request):
    if request.method == 'POST':
        intention = request.POST.get('intention')
        user_profile = UserProfile.objects.get(user=request.user)
        user_profile.intention = intention
        user_profile.save()
        initial_data = create_initial_data(ChatGPT(), intention, DEFAULT_TAGS, DEFAULT_LINK_TYPES)
        tags = initial_data.get('tags')
        if not tags:
            tags = DEFAULT_TAGS
        link_types = initial_data.get('link_types')
        if not link_types:
            link_types = DEFAULT_LINK_TYPES
        for tag_name in tags:
            Tag.objects.create(name=tag_name, user=request.user)
        for forward_name, reverse_name in link_types:
            LinkType.objects.create(name=forward_name, reverse_name=reverse_name, user=request.user)
        return redirect('home')
    return render(request, 'auth/intentions_form.html')


@login_required
def home_view(request):
    tag = request.user.tag_set.all().first()
    if tag:
        return redirect(tag.get_absolute_url())
    return redirect('memo_create')

