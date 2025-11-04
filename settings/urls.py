from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    path('', views.settings_list, name='index'),
    path('business/', views.business_settings, name='business'),
    path('barcode/', views.barcode_settings, name='barcode'),
    path('users/', views.user_management, name='users'),
    path('backup/', views.backup_restore, name='backup'),
    path('backup/settings/', views.backup_settings, name='backup_settings'),
    path('backup/download/<str:filename>/', views.download_backup, name='download_backup'),
    path('theme/', views.theme_settings, name='theme'),
    path('email/', views.email_settings, name='email'),
    path('voice/', views.voice_assistant, name='voice'),
]