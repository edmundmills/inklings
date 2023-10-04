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
from django.urls import path

from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/signup/', views.signup_view, name='signup'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('memos', views.MemoListView.as_view(), name='home'),
    path('memo/<int:pk>/', views.MemoDetailView.as_view(), name='view_memo'),
    path('memos/create', views.create_memo, name='create_memo'),
    path('memo/<int:pk>/process/', views.process_memo, name='process_memo'),
    path('tag/<int:pk>/', views.TagDetailView.as_view(), name='view_tag'),
    path('inkling/<int:pk>/', views.InklingDetailView.as_view(), name='view_inkling'),
]
