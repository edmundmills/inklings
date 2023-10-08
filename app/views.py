import itertools

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import (CreateView, DetailView, ListView, UpdateView,
                                  View)
from pgvector.django import CosineDistance

from .ai import create_inklings, get_tags, get_tags_and_title
from .forms import LinkTypeForm, MemoForm, TagForm
from .helpers import generate_embedding
from .models import Inkling, Link, LinkType, Memo, NodeModel, Query, Tag, User


def common_context(request, object = None) -> dict:
    context = dict()
    context.update(get_all(request.user)) # type: ignore
    if object is not None:
        context.update(get_similar(object, request.user)) # type: ignore
        context['feed_objects'] = [dict(object=o, type=str(type(o).__name__)) for o in itertools.chain(context['similar_inklings'], context['similar_memos'])]
    context['link_types'] = LinkType.objects.filter(user=request.user)
    return context


@method_decorator(login_required, name='dispatch')
class FeedView(DetailView):
    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        object = self.object # type: ignore
        context = super().get_context_data(**kwargs)
        context.update(common_context(self.request, object))
        if isinstance(object, NodeModel):
            context['link_groups'] = object.get_link_groups()
        return context


@method_decorator(login_required, name='dispatch')
class MemoFeedView(FeedView):
    model = Memo
    template_name = 'feed_memo.html'


@method_decorator(login_required, name='dispatch')
class InklingFeedView(FeedView):
    model = Inkling
    template_name = 'feed_inkling.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link_groups'] = self.object.get_link_groups(self.object) # type: ignore
        return context


@method_decorator(login_required, name='dispatch')
class TagFeedView(FeedView):
    model = Tag
    template_name = 'feed_tag.html'


@method_decorator(login_required, name='dispatch')
class QueryFeedView(FeedView):
    model = Query # type: ignore
    template_name = 'feed_query.html'

    def get_object(self, queryset=None):
        query = self.request.GET.get('query')
        embedding = generate_embedding(query)
        return Query(query, embedding) # type: ignore


@method_decorator(login_required, name='dispatch')
class MemoListView(ListView):
    model = Memo
    template_name = 'home.html'
    
    def get_queryset(self):
        return Memo.objects.filter(user=self.request.user).order_by('-created_at')

    def dispatch(self, request, *args, **kwargs):
        memos = Memo.objects.filter(user=self.request.user).order_by('-updated_at') 
        if memos.exists():
            return redirect('view_memo', memos[0].pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(common_context(self.request))
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


@method_decorator(login_required, name='dispatch')
class MemoCreateAndRedirectToEditView(View):
    def get(self, request, *args, **kwargs):
        memo = Memo.objects.create(title='Untitled', content='', user=request.user)
        return redirect(reverse('edit_memo', args=[memo.id])) # type: ignore


@method_decorator(login_required, name='dispatch')
class MemoEditView(UpdateView):
    model = Memo
    fields = ['title', 'content']
    template_name = 'edit_memo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(common_context(self.request, self.object)) # type: ignore
        return context

    def form_valid(self, form):
        memo = form.save(commit=False)
        memo.embedding = generate_embedding(memo.content)
        title = None if memo.title == "Untitled" else memo.title
        if (not title) or (not memo.tags.exists()):
            user_tags = self.request.user.tag_set.all() # type: ignore
            ai_content = get_tags_and_title(memo.content, title, user_tags)
            memo.create_tags(ai_content['tags'])

            if not title:
                title = ai_content.get('title')
            if title:
                memo.title = title

        memo.save()  # Save to the database
        return redirect('view_memo', memo.id)



@login_required
@require_POST
def create_inkling(request):
    content = request.POST.get('content')

    if not content:
        return redirect('home')
    
    user_tags = request.user.tag_set.all() # type: ignore
    ai_content = get_tags_and_title(content, None, user_tags)
    inkling = Inkling.objects.create(content=content, user=request.user)
    inkling.create_tags(ai_content['tags'])

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
    embedding = tag.embedding
    tag.delete()
    similar_tag = Tag.objects.filter(user=request.user).alias(distance=CosineDistance('embedding', embedding)).order_by('distance')[0]
    return redirect('view_tag', similar_tag.pk)


@login_required
def delete_memo(request, pk):
    memo = get_object_or_404(Memo, id=pk, user=request.user)
    embedding = memo.embedding
    memo.delete()
    similar_memo = Memo.objects.filter(user=request.user).alias(distance=CosineDistance('embedding', embedding)).order_by('distance')[0]
    return redirect('view_memo', similar_memo.pk)


@login_required
def process_memo(request, pk):
    memo = get_object_or_404(Memo, id=pk, user=request.user)
    if len(memo.inkling_set.all()): # type: ignore
        return redirect('view_memo', memo.pk)
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
                user_tags = request.user.tag_set.all() # type: ignore
                created_tags = get_tags([i.content for i in inklings], user_tags)
                for tags, inkling in zip(created_tags, inklings):
                    inkling.create_tags(tags)
            return redirect('view_memo', memo.id)  # type: ignore
    return redirect('home')
    



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


@login_required
def create_link(request):
    if request.method != 'POST':
        return redirect(request.META['HTTP_REFERER'])
    source_inkling_id = request.POST.get('source_inkling_id')
    target_inkling_id = request.POST.get('target_inkling_id')
    link_type_id: str = request.POST.get('linkType')
    if link_type_id.endswith('_reverse'):
        source_inkling_id, target_inkling_id = target_inkling_id, source_inkling_id
        link_type_id = link_type_id.removesuffix('_reverse')
    link_type = LinkType.objects.get(pk=link_type_id)
    link = Link(
        source_inkling_id=source_inkling_id,
        target_inkling_id=target_inkling_id,
        link_type=link_type,
    )
    link.save()
    # messages.success(request, "Link created successfully!")
    return redirect(request.META['HTTP_REFERER'])


@login_required
def create_link_type(request):
    if request.method != 'POST':
        redirect(request.META['HTTP_REFERER'])
    name = request.POST.get('name')
    reverse_name = request.POST.get('reverse_name')
    link_type = LinkType(
        name=name,
        reverse_name=reverse_name,
        user=request.user
    )
    link_type.save()
    return redirect(request.META['HTTP_REFERER'])


@method_decorator(login_required, name='dispatch')
class LinkTypeListView(ListView):
    model = LinkType
    template_name = 'link_type_list.html'
    
    def get_queryset(self):
        return LinkType.objects.filter(user=self.request.user).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(common_context(self.request))
        return context

@login_required
@require_POST
def edit_link_type(request, pk):
    link_type = get_object_or_404(LinkType, pk=pk)
    if request.method == 'POST':
        form = LinkTypeForm(request.POST, instance=link_type)  # Use your LinkType form if available
        if form.is_valid():
            form.save()
            return redirect('link_types')  # Redirect to the list of link types or another appropriate page
    else:
        form = LinkTypeForm(instance=link_type)  # Use your LinkType form if available

    return render(request, 'edit_link_type.html', {'form': form, 'link_type': link_type})

@login_required
def delete_link_type(request, pk):
    link_type = get_object_or_404(LinkType, pk=pk)
    link_type.delete()
    return redirect('link_types')  # Redirect to the list of link types or another appropriate page
