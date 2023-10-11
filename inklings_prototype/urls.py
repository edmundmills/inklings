from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from app import views

urlpatterns = [
    path('', views.new_feed_view, name='home'),
    
    path('admin/', admin.site.urls),
    path('accounts/signup/', views.signup_view, name='signup'),
    path('accounts/intention/', views.get_intention, name='get_intention'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='auth/login.html', next_page='home'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('memos/', views.MemoListView.as_view(), name='memos'),
    path('memo/<int:pk>/', views.MemoFeedView.as_view(), name='memo_view'),
    path('memos/create/', views.MemoCreateAndRedirectToEditView.as_view(), name='memo_create'),
    path('memo/<int:pk>/edit/', views.MemoEditView.as_view(), name='memo_edit'),
    path('memo/<int:pk>/delete/', views.DeleteMemoView.as_view(), name='memo_delete'),
    
    path('inklings/', views.InklingListView.as_view(), name='inklings'),
    path('inkling/<int:pk>/', views.InklingFeedView.as_view(), name='inkling_view'),
    path('inkling/<int:pk>/edit/', views.EditInklingView.as_view(), name='inkling_edit'),
    path('inkling/<int:pk>/delete/', views.DeleteInklingView.as_view(), name='inkling_delete'),
    path('inklings/create/', views.CreateInklingView.as_view(), name='inkling_create'),
    path('inklings/create_with_link/', views.create_inkling_and_link, name='inkling_create_and_link'),
    
    path('references/', views.ReferenceListView.as_view(), name='references'),
    path('references/create', views.ReferenceCreateView.as_view(), name='reference_create'),
    path('reference/<int:pk>/', views.ReferenceFeedView.as_view(), name='reference_view'),
    path('reference/<int:pk>/edit/', views.EditReferenceView.as_view(), name='reference_edit'),
    path('reference/<int:pk>/delete/', views.DeleteReferenceView.as_view(), name='reference_delete'),

    path('search/', views.QueryFeedView.as_view(), name='search'),
    
    path('links/', views.LinkListView.as_view(), name='links'),
    path('links/create/', views.CreateLinkView.as_view(), name='link_create'),
    path('link/<int:pk>/delete/', views.DeleteLinkView.as_view(), name='link_delete'),
    
    path('link_types/', views.LinkTypeListView.as_view(), name='link_types'),
    path('link_types/create', views.CreateLinkTypeView.as_view(), name='link_type_create'),
    path('link_type/<int:pk>/edit/', views.EditLinkTypeView.as_view(), name='link_type_edit'),
    path('link_type/<int:pk>/delete/', views.DeleteLinkTypeView.as_view(), name='link_type_delete'),

    path('tag/<int:pk>/', views.TagFeedView.as_view(), name='tag_view'),
    path('tag/<int:pk>/delete/', views.DeleteTagView.as_view(), name='tag_delete'),
    path('tag/<int:pk>/edit/', views.UpdateTagView.as_view(), name='tag_update'),
    path('tags/', views.TagListView.as_view(), name='tags'),
    path('tags/add/', views.add_tag, name='tag_add'),
    path('tags/merge/', views.merge_tags, name='tags_merge'),

    path('martor/', include('martor.urls')),
]
