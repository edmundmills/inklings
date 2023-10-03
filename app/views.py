from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, UpdateView

from .ai import create_inklings, get_keywords_and_title
from .forms import InklingFormset, MemoForm
from .helpers import create_tags
from .models import Inkling, Memo, Tag


@method_decorator(login_required, name='dispatch')
class MemoListView(ListView):
    model = Memo
    template_name = 'home.html'
    
    def get_queryset(self):
        return Memo.objects.filter(user=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['memos'] = Memo.objects.filter(user=self.request.user).order_by('-created_at')
        context['tags'] =  Tag.objects.filter(user=self.request.user).order_by('name')
        return context


@method_decorator(login_required, name='dispatch')
class MemoDetailView(DetailView):
    model = Memo
    template_name = 'view_memo.html'

    def get_queryset(self):
        return Memo.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['memos'] = Memo.objects.filter(user=self.request.user).order_by('-created_at')
        context['tags'] =  Tag.objects.filter(user=self.request.user).order_by('name')
        return context


@method_decorator(login_required, name='dispatch')
class TagDetailView(DetailView):
    model = Tag
    template_name = 'view_tag.html'
    
    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['memos'] = Memo.objects.filter(user=self.request.user).order_by('-created_at')
        context['tags'] =  Tag.objects.filter(user=self.request.user).order_by('name')
        return context


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


@login_required
@require_POST
def create_memo(request):
    title = request.POST.get('title')
    content = request.POST.get('content')

    if not content:
        return redirect('home')
    
    user_tags = [t.name for t in Tag.objects.filter(user=request.user).order_by('name')]
    ai_content = get_keywords_and_title(content, title, user_tags)
    if not title:
        title = ai_content.get('title')
    if not title:
        return redirect('home')

    memo = Memo.objects.create(title=title, content=content, user=request.user)
    create_tags(ai_content['tags'], memo)

    inklings = create_inklings(text=content, title=title, existing_tags=user_tags)
    for inkling in inklings:
        inkling_tags = inkling.pop('tags')
        inkling = Inkling.objects.create(**inkling, user=request.user, memo=memo)
        create_tags(inkling_tags, inkling)

    return redirect('process_memo', memo.id)  # type: ignore


@login_required
def process_memo(request, pk):
    memo = get_object_or_404(Memo, id=pk, user=request.user)

    if request.method == 'POST':
        form = MemoForm(request.POST, instance=memo)
        formset = InklingFormset(request.POST, instance=memo)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('view_memo', memo.id)  # type: ignore
    else:
        form = MemoForm(instance=memo)
        formset = InklingFormset(instance=memo)

    return render(request, 'process_memo.html', {'form': form, 'formset': formset})
