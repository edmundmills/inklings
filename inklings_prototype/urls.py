"""
URL configuration for inklings_prototype project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/signup/', views.signup_view, name='signup'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', views.MemoListView.as_view(), name='home'),
    path('memo/<int:pk>/', views.MemoDetailView.as_view(), name='view_memo'),
    path('memo/<int:pk>/delete/', views.delete_memo, name='delete_memo'),
    path('memo/<int:pk>/edit/', views.MemoEditView.as_view(), name='edit_memo'),
    path('memos/new/', views.MemoCreateAndRedirectToEditView.as_view(), name='new_memo'),
    path('memo/<int:pk>/process/', views.process_memo, name='process_memo'),
    path('tag/<int:pk>/', views.TagDetailView.as_view(), name='view_tag'),
    path('tag/<int:pk>/delete/', views.delete_tag, name='delete_tag'),
    path('tag/<int:pk>/update/', views.update_tag, name='update_tag'),
    path('inkling/<int:pk>/', views.InklingDetailView.as_view(), name='view_inkling'),
    path('inkling/<int:pk>/delete/', views.delete_inkling, name='delete_inkling'),
    path('inklings/create/', views.create_inkling, name='create_inkling'),
    path('search/', views.search, name='search'),
    path('merge_tags/', views.merge_tags, name='merge_tags'),
    path('martor/', include('martor.urls')),
]
