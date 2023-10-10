from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DeleteView, UpdateView

from app.embeddings import generate_embedding
from app.forms import AddTagForm, TagForm
from app.mixins import SimilarObjectMixin, UserScopedMixin
from app.models import Inkling, Memo, Tag


class DeleteTagView(SimilarObjectMixin, DeleteView, UserScopedMixin):
    model = Tag
    success_url = '/'
        
    def get_success_url(self):
        """
        Redirect to the most similar tag after deletion.
        """
        similar_tag = self.get_similar_object()
        if not similar_tag:
            return reverse('home')
        return reverse('tag_view', args=[similar_tag.pk])


class UpdateTagView(LoginRequiredMixin, UpdateView):
    model = Tag
    form_class = TagForm
    template_name = 'tag/edit.html'  # You'd have to specify the path to your template
    context_object_name = 'tag'
    pk_url_kwarg = 'pk'  # This captures the primary key from the URL

    def get_queryset(self):
        # Ensuring that only tags owned by the logged-in user can be edited
        return super().get_queryset().filter(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy('tag_view', args=[self.object.pk]) # type: ignore
    
    def form_invalid(self, form):
        # Redirect to home on invalid form submission
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
    form = AddTagForm(request.POST)
    if not form.is_valid():
        return redirect('/')
    tag = get_object_or_404(Tag, id=form.cleaned_data['tag_id'])
    target_class = form.cleaned_data['target_class_name']
    target_object = get_object_or_404(target_class, id=form.cleaned_data['target_id'])
    target_object.tags.add(tag)
    return redirect(reverse('tag_view', args=[tag.pk]))
