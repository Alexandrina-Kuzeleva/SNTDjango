from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('management/', views.management, name='management'),
    path('documents/', views.documents_list, name='documents'),
    path('info/', views.info, name='info'),
    path('announcements/', views.announcements, name='announcements'),
    path('contacts/', views.contacts, name='contacts'),
    
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    path('news/manage/', views.news_manage, name='news_manage'),
    path('news/create/', views.news_create, name='news_create'),
    path('news/<int:pk>/edit/', views.news_edit, name='news_edit'),
    path('news/<int:pk>/delete/', views.news_delete, name='news_delete'),
    path('news/<int:pk>/', views.news_detail, name='news_detail'),
    path('announcement/create/', views.announcement_create, name='announcement_create'),

    path('documents/', views.documents_list, name='documents'),
    path('documents/upload/', views.document_upload, name='document_upload'),
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/<int:pk>/download/', views.document_download, name='document_download'),
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),
    
    path('debts/upload/', views.upload_debts, name='upload_debts'),
    path('debts/summary/', views.debt_summary, name='debt_summary'),
    path('debts/history/<int:user_id>/', views.debt_history, name='debt_history'),
    path('debts/my-history/', views.debt_history, name='my_debt_history'),
]