from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from app import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    
    path('admin/', admin.site.urls),
    path('accounts/signup/', views.signup_view, name='signup'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html', next_page='home'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('memos/', views.MemoListView.as_view(), name='memos'),
    path('memo/<int:pk>/', views.MemoFeedView.as_view(), name='view_memo'),
    path('memos/new/', views.MemoCreateAndRedirectToEditView.as_view(), name='new_memo'),
    path('memo/<int:pk>/edit/', views.MemoEditView.as_view(), name='edit_memo'),
    path('memo/<int:pk>/delete/', views.DeleteMemoView.as_view(), name='delete_memo'),
    
    path('inklings/', views.InklingListView.as_view(), name='inklings'),
    path('inkling/<int:pk>/', views.InklingFeedView.as_view(), name='view_inkling'),
    path('inkling/<int:pk>/delete/', views.DeleteInklingView.as_view(), name='delete_inkling'),
    path('inklings/create/', views.CreateInklingView.as_view(), name='create_inkling'),
    
    path('references/', views.ReferenceListView.as_view(), name='references'),

    path('search/', views.QueryFeedView.as_view(), name='search'),
    
    path('links/create/', views.CreateLinkView.as_view(), name='create_link'),
    path('link/<int:pk>/delete/', views.DeleteLinkView.as_view(), name='delete_link'),
    
    path('link_types/', views.LinkTypeListView.as_view(), name='link_types'),
    path('link_types/create', views.CreateLinkTypeView.as_view(), name='create_link_type'),
    path('link_type/<int:pk>/edit/', views.EditLinkTypeView.as_view(), name='edit_link_type'),
    path('link_type/<int:pk>/delete/', views.DeleteLinkTypeView.as_view(), name='delete_link_type'),

    path('tag/<int:pk>/', views.TagFeedView.as_view(), name='view_tag'),
    path('tag/<int:pk>/delete/', views.DeleteTagView.as_view(), name='delete_tag'),
    path('tag/<int:pk>/edit/', views.UpdateTagView.as_view(), name='update_tag'),
    path('tags/merge/', views.merge_tags, name='merge_tags'),

    path('martor/', include('martor.urls')),
]
