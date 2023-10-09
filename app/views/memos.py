from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DeleteView, UpdateView, View

from app.mixins import (GenerateTitleAndTagsMixin, SimilarObjectMixin,
                        UserScopedMixin)
from app.models import Memo


class MemoCreateAndRedirectToEditView(View, LoginRequiredMixin):
    def get(self, request, *args, **kwargs):
        memo = Memo.objects.create(title='Untitled', content='', user=request.user)
        return redirect(reverse('memo_edit', args=[memo.id])) # type: ignore


class MemoEditView(LoginRequiredMixin, UserScopedMixin, GenerateTitleAndTagsMixin, UpdateView):
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
        return reverse('memo_view', args=[similar_object.pk])



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