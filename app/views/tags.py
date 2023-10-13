from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DeleteView, UpdateView

from app.embeddings import generate_embedding
from app.forms import TagForm
from app.mixins import RedirectBackMixin, UserScopedMixin
from app.models import Inkling, Memo, Tag


class DeleteTagView(LoginRequiredMixin, RedirectBackMixin, UserScopedMixin, DeleteView):
    model = Tag
    success_url = '/'


class UpdateTagView(LoginRequiredMixin, UserScopedMixin, UpdateView):
    model = Tag
    form_class = TagForm

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy('tag_view', args=[self.object.pk]) # type: ignore
    
    def form_invalid(self, form):
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

    return redirect('tag_view', current_tag.id)  # type: ignore

@login_required
def add_tag(request):
    if request.method != 'POST':
        return redirect('/')
    form = TagForm(request.POST)
    if not form.is_valid():
        return redirect('/')
    tag, _created = Tag.objects.get_or_create(name=form.cleaned_data['name'], user=request.user)
    target_class = form.cleaned_data['target_class_name']
    if target_class is not None:
        target_object = get_object_or_404(target_class, id=form.cleaned_data['target_id'])
        target_object.tags.add(tag)
        return redirect(target_object.get_absolute_url())
    return redirect(tag.get_absolute_url())
