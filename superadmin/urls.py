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
]
