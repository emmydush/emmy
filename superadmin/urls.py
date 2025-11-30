from django.urls import path
from . import views

app_name = "superadmin"

urlpatterns = [
    path("", views.SuperAdminDashboardView.as_view(), name="dashboard"),
    path(
        "businesses/",
        views.BusinessManagementView.as_view(),
        name="business_management",
    ),
    path(
        "business-register/",
        views.business_register_view,
        name="business_register",
    ),
    path(
        "business-registration-success/",
        views.business_registration_success_view,
        name="business_registration_success",
    ),
    path(
        "subscriptions/",
        views.SubscriptionManagementView.as_view(),
        name="subscription_management",
    ),
    path("logs/", views.SystemLogsView.as_view(), name="system_logs"),
    path(
        "communication/",
        views.CommunicationCenterView.as_view(),
        name="communication_center",
    ),
    path("api-monitoring/", views.APIMonitoringView.as_view(), name="api_monitoring"),
    path("email-settings/", views.EmailSettingsView.as_view(), name="email_settings"),
    
    # Business management URLs
    path(
        "businesses/<int:business_pk>/suspend/",
        views.suspend_business_view,
        name="suspend_business",
    ),
    path(
        "businesses/<int:business_pk>/activate/",
        views.activate_business_view,
        name="activate_business",
    ),
    path(
        "businesses/<int:business_pk>/approve/",
        views.approve_business_view,
        name="approve_business",
    ),
    path(
        "businesses/<int:business_pk>/delete/",
        views.delete_business_view,
        name="delete_business",
    ),
    
    # Branch management URLs
    path(
        "businesses/<int:business_pk>/branches/",
        views.branch_list_view,
        name="branch_list",
    ),
    path(
        "businesses/<int:business_pk>/branches/create/",
        views.branch_create_view,
        name="branch_create",
    ),
    path(
        "businesses/<int:business_pk>/branches/<int:pk>/update/",
        views.branch_update_view,
        name="branch_update",
    ),
    path(
        "businesses/<int:business_pk>/branches/<int:pk>/delete/",
        views.branch_delete_view,
        name="branch_delete",
    ),
    
    # Branch request URLs
    path(
        "branch-requests/",
        views.branch_request_list_view,
        name="branch_request_list",
    ),
    path(
        "branch-requests/create/",
        views.branch_request_create_view,
        name="branch_request_create",
    ),
    path(
        "branch-requests/approval/",
        views.branch_request_approval_list_view,
        name="branch_request_approval_list",
    ),
    path(
        "branch-requests/<int:pk>/approve/",
        views.branch_request_approve_view,
        name="branch_request_approve",
    ),
    path(
        "branch-requests/<int:pk>/",
        views.branch_request_detail_view,
        name="branch_request_detail",
    ),
]