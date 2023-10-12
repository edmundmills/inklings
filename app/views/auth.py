from typing import Any

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import (CreateView, DetailView, ListView, UpdateView,
                                  View)

from app.config import DEFAULT_LINK_TYPES, DEFAULT_TAGS
from app.embeddings import generate_embedding
from app.forms import FriendRequestForm, UserCreationForm
from app.mixins import UserScopedMixin
from app.models import FriendRequest, LinkType, Memo, Tag, User, UserInvite
from app.prompting import ChatGPT, create_initial_data
from app.tables import (FriendsTable, ReceivedFriendRequestTable,
                        SentFriendRequestTable, SentInvitesTable)


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            invite_token = form.cleaned_data.get('invite_token')
            invites = []
            if invite_token:
                invites.append(get_object_or_404(UserInvite, token=invite_token))
            invites.extend(UserInvite.objects.filter(email=user.email).all())
            for invite in invites:
                inviter = invite.inviter
                inviter.send_friend_request(user)
                invite.delete()
            login(request, user)
            return redirect('get_intention')
    else:
        invite_token = request.GET.get('invite_token')
        form = UserCreationForm(initial={'invite_token': invite_token})
    return render(request, 'auth/signup.html', {'form': form})

@login_required
def get_intention(request):
    if request.method == 'POST':
        user = request.user
        intention = request.POST.get('intention')
        user.intention = intention
        user.intention_embedding = generate_embedding(intention)
        user.save()
        initial_data = create_initial_data(ChatGPT(), intention, DEFAULT_TAGS, DEFAULT_LINK_TYPES)
        tags = initial_data.get('tags')
        if not tags:
            tags = DEFAULT_TAGS
        link_types = initial_data.get('link_types')
        if not link_types:
            link_types = DEFAULT_LINK_TYPES
        for tag_name in tags:
            Tag.objects.create(name=tag_name, user=user)
        for forward_name, reverse_name in link_types:
            LinkType.objects.create(name=forward_name, reverse_name=reverse_name, user=user)
        return redirect('home')
    return render(request, 'auth/intentions_form.html')

@login_required
def invite_user(request):
    if request.method != 'POST':
            return redirect('home')
    form = FriendRequestForm(request.POST)
    if not form.is_valid():
            return redirect('home')
    email = form.cleaned_data.get('email')
    receiver = User.objects.filter(email=email).exclude(pk=request.user.pk).first()
    if receiver:
        request.user.send_friend_request(receiver)
        # messages.success(request, "Friend request sent.")
    else:
        UserInvite.objects.create(inviter=request.user, email=email)
    return redirect('friends')


class FriendsListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'user/friends_list.html'

    def get_queryset(self):
        return self.request.user.friends.all() # type: ignore

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user: User = self.request.user # type: ignore
        context['friends_table'] = FriendsTable(user.friends.all())
        context['sent_friend_requests_table'] = SentFriendRequestTable(FriendRequest.objects.filter(sender=user))
        context['received_friend_requests_table'] = ReceivedFriendRequestTable(FriendRequest.objects.filter(receiver=user))
        context['sent_invites_table'] = SentInvitesTable(UserInvite.objects.filter(inviter=user))
        return context


@login_required
def accept_friend_request(request, pk):
    friend_request = get_object_or_404(FriendRequest, id=pk, receiver=request.user)
    request.user.accept_friend_request(friend_request.sender)
    messages.success(request, f'You are now friends with {friend_request.sender.username}!')
    friend_request.delete()
    return redirect('friends')

@login_required
def delete_friend_request(request, pk):
    friend_request = get_object_or_404(FriendRequest, id=pk)
    if friend_request.sender == request.user:
        friend_request.delete()
        messages.info(request, f'Friend request from {friend_request.sender.username} has been deleted.')
    elif friend_request.receiver == request.user:
        friend_request.delete()
        messages.info(request, f'Friend request to {friend_request.receiver.username} has been deleted.')
    else:
        messages.error(request, f'You do not have permission to delete this friend request.')
    return redirect('friends')
