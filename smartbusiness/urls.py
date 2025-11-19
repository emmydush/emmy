from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("authentication.urls")),
    path("accounts/", include("allauth.urls")),
    path("superadmin/", include("superadmin.urls")),
    path("", include("products.urls")),
    path("sales/", include("sales.urls")),
    path("customers/", include("customers.urls")),
    path("suppliers/", include("suppliers.urls")),
    path("expenses/", include("expenses.urls")),
    path("reports/", include("reports.urls")),
    path("settings/", include("settings.urls")),
    path("notifications/", include("notifications.urls")),
]
