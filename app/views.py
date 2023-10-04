from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, UpdateView
from pgvector.django import CosineDistance

from .ai import create_inklings, get_tags, get_tags_and_title
from .forms import InklingFormset, MemoForm, TagForm
from .helpers import create_tags, generate_embedding, get_user_tags
from .models import Inkling, Memo, Tag

FILTER_THRESHOLD = 0.7

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
class InklingDetailView(DetailView):
    model = Inkling
    template_name = 'view_inkling.html'

    def get_queryset(self):
        return Inkling.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tags'] =  Tag.objects.filter(user=self.request.user).order_by('name')
        context['similar_inklings'] =  Inkling.objects.filter(user=self.request.user).alias(distance=CosineDistance('embedding', self.object.embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance')[1:6] # type: ignore
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
        context['similar_tags'] =  Tag.objects.filter(user=self.request.user).alias(distance=CosineDistance('embedding', self.object.embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance')[1:20] # type: ignore
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
    
    user_tags = get_user_tags(request.user)
    ai_content = get_tags_and_title(content, title, user_tags)
    if not title:
        title = ai_content.get('title')
    if not title:
        return redirect('home')

    memo = Memo.objects.create(title=title, content=content, user=request.user)
    create_tags(ai_content['tags'], memo)
    return redirect('process_memo', memo.id)  # type: ignore


@login_required
@require_POST
def create_inkling(request):
    content = request.POST.get('content')

    if not content:
        return redirect('home')
    
    user_tags = get_user_tags(request.user)
    ai_content = get_tags_and_title(content, None, user_tags)
    inkling = Inkling.objects.create(content=content, user=request.user)
    create_tags(ai_content['tags'], inkling)

    return redirect('view_inkling', inkling.id)  # type: ignore

@login_required
def delete_inkling(request, pk):
    inkling = get_object_or_404(Inkling, id=pk, user=request.user)
    inkling.delete()
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer) if referer else redirect('/')

@login_required
def delete_tag(request, pk):
    tag = get_object_or_404(Tag, id=pk, user=request.user)
    tag.delete()
    return redirect('/')

@login_required
def delete_memo(request, pk):
    memo = get_object_or_404(Memo, id=pk, user=request.user)
    memo.delete()
    return redirect('/')

@login_required
def process_memo(request, pk):
    memo = get_object_or_404(Memo, id=pk, user=request.user)
    if len(memo.inkling_set.all()): # type: ignore
        return redirect('view_memo', memo.id) # type: ignore
    if request.method == 'GET':
        ideas = create_inklings(memo.content, memo.title)
        initial_ideas = [{'content': idea} for idea in ideas]
        form = MemoForm(instance=memo)
        formset = InklingFormset(instance=memo, initial=initial_ideas)
        return render(request, 'process_memo.html', {'form': form, 'formset': formset})
    elif request.method == 'POST':
        form = MemoForm(request.POST, instance=memo)
        formset = InklingFormset(request.POST, instance=memo)
        if not formset.is_valid():
            print(formset.errors)
        if formset.is_valid():
            inklings = formset.save(commit=False)
            for inkling in inklings:
                inkling.user = request.user
                inkling.save()

            if inklings:
                user_tags = get_user_tags(request.user)
                created_tags = get_tags([i.content for i in inklings], user_tags)
                for tags, inkling in zip(created_tags, inklings):
                    create_tags(tags, inkling)
            return redirect('view_memo', memo.id)  # type: ignore
    return redirect('home')
    

@login_required
def search(request):
    MAX_TAGS = 10
    query = request.GET.get('query', '')
    embedding = generate_embedding(query)
    inklings = Inkling.objects.filter(user=request.user).alias(distance=CosineDistance('embedding', embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance')
    tags = Tag.objects.filter(user=request.user).alias(distance=CosineDistance('embedding', embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance')[:MAX_TAGS]
    memos = Memo.objects.filter(user=request.user).alias(distance=CosineDistance('embedding', embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance')
    return render(request, 'search.html', dict(query=query, inklings=inklings, tags=tags, memos=memos))


@login_required
def update_tag(request, pk):
    tag = get_object_or_404(Tag, id=pk, user=request.user)

    if request.method == "POST":
        form = TagForm(request.POST, instance=tag)

        if form.is_valid():
            form.save()
            return redirect('view_tag', pk)

    return redirect('home')


@login_required
def merge_tags(request):
    if request.method != "POST":
        return redirect('home')
    
    current_tag_id = request.POST.get('currentTag')
    tag_to_merge_id = request.POST.get('tagToMerge')
    new_name = request.POST.get('newName', '').strip()

    current_tag = get_object_or_404(Tag, id=current_tag_id)
    tag_to_merge = get_object_or_404(Tag, id=tag_to_merge_id)

    # Update Memo objects
    memos_with_merge_tag = Memo.objects.filter(tags=tag_to_merge)
    for memo in memos_with_merge_tag:
        memo.tags.remove(tag_to_merge)
        memo.tags.add(current_tag, through_defaults={})

    # Update Inkling objects
    inklings_with_merge_tag = Inkling.objects.filter(tags=tag_to_merge)
    for inkling in inklings_with_merge_tag:
        inkling.tags.remove(tag_to_merge)
        inkling.tags.add(current_tag, through_defaults={})

    tag_to_merge.delete()

    if new_name:
        current_tag.name = new_name
        current_tag.embedding = generate_embedding(new_name)
        current_tag.save()

    return redirect('view_tag', current_tag.id)  # type: ignore
