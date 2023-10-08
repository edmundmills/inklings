from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView, View)
from pgvector.django import CosineDistance

from app.mixins import (GenerateTitleAndTagsMixin, SimilarObjectMixin,
                        UserScopedMixin)
from app.models import Memo


@method_decorator(login_required, name='dispatch')
class MemoListView(ListView):
    model = Memo
    template_name = 'layouts/home.html'
    
    def get_queryset(self):
        return Memo.objects.filter(user=self.request.user).order_by('-created_at')

    def dispatch(self, request, *args, **kwargs):
        memos = Memo.objects.filter(user=self.request.user).order_by('-updated_at') 
        if memos.exists():
            return redirect('view_memo', memos[0].pk)
        return super().dispatch(request, *args, **kwargs)

    

class MemoCreateAndRedirectToEditView(View, LoginRequiredMixin):
    def get(self, request, *args, **kwargs):
        memo = Memo.objects.create(title='Untitled', content='', user=request.user)
        return redirect(reverse('edit_memo', args=[memo.id])) # type: ignore


class MemoEditView(UpdateView, LoginRequiredMixin, UserScopedMixin, GenerateTitleAndTagsMixin):
    model = Memo
    fields = ['title', 'content']
    template_name = 'memo/edit.html'


class DeleteMemoView(SimilarObjectMixin, DeleteView, UserScopedMixin):
    model = Memo
    success_url = '/'
        
    def get_success_url(self):
        """
        Redirect to the most similar tag after deletion.
        """
        similar_object = self.get_similar_object()
        if not similar_object:
            return reverse('home')
        return reverse('view_memo', args=[similar_object.pk])



# @login_required
# def process_memo(request, pk):
#     memo = get_object_or_404(Memo, id=pk, user=request.user)
#     if len(memo.inkling_set.all()): # type: ignore
#         return redirect('view_memo', memo.pk)
#     if request.method == 'GET':
#         ideas = create_inklings(memo.content, memo.title)
#         initial_ideas = [{'content': idea} for idea in ideas]
#         form = MemoForm(instance=memo)
#         formset = InklingFormset(instance=memo, initial=initial_ideas)
#         return render(request, 'process_memo.html', {'form': form, 'formset': formset})
#     elif request.method == 'POST':
#         form = MemoForm(request.POST, instance=memo)
#         formset = InklingFormset(request.POST, instance=memo)
#         if not formset.is_valid():
#             print(formset.errors)
#         if formset.is_valid():
#             inklings = formset.save(commit=False)
#             for inkling in inklings:
#                 inkling.user = request.user
#                 inkling.save()

#             if inklings:
#                 user_tags = request.user.tag_set.all() # type: ignore
#                 created_tags = get_tags([i.content for i in inklings], user_tags)
#                 for tags, inkling in zip(created_tags, inklings):
#                     inkling.create_tags(tags)
#             return redirect('view_memo', memo.id)  # type: ignore
#     return redirect('home')