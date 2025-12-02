from django.urls import path
from . import views

app_name = "settings"

urlpatterns = [
    path("", views.settings_list, name="index"),
    path("business/", views.business_settings, name="business"),
    path("barcode/", views.barcode_settings, name="barcode"),
    path("users/", views.user_management, name="users"),
    path("backup/", views.backup_restore, name="backup"),
    path("backup/settings/", views.backup_settings, name="backup_settings"),
    path(
        "backup/download/<str:filename>/", views.download_backup, name="download_backup"
    ),
    path("email/", views.email_settings, name="email"),
    path("audit-logs/", views.audit_logs, name="audit_logs"),
    path("bulky-upload/", views.bulky_upload, name="bulky_upload"),
    path(
        "bulky-upload/process/<str:filename>/",
        views.process_bulky_file,
        name="process_bulky_file",
    ),
    path(
        "bulky-upload/delete/<str:filename>/",
        views.delete_bulky_file,
        name="delete_bulky_file",
    ),
]
