from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from .models import Memo


@method_decorator(login_required, name='dispatch')
class MemoListView(ListView):
    model = Memo
    template_name = 'home.html'
    
    def get_queryset(self):
        return Memo.objects.filter(user=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['memos'] = Memo.objects.filter(user=self.request.user).order_by('-created_at')
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
    if title and content:
        memo = Memo.objects.create(title=title, content=content, user=request.user)
        return redirect('view_memo', memo.id)  # type: ignore

    return redirect('home')
