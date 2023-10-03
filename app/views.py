from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render

from .models import Memo


@login_required
def home_view(request):
    # memos = Memo.objects.filter(user=request.user).order_by('-created_at')
    memos = []
    return render(request, 'home.html', {'memos': memos})

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in.
            login(request, user)
            return redirect('home')  # or your named URL for the home page
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})
