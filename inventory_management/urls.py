from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from superadmin.views import business_selection_view


# Redirect root URL to login page
def root_redirect(request):
    return redirect("login")


urlpatterns = [
    path("", root_redirect, name="home"),
    path("api/v1/", include("api.urls")),
    path("dashboard/", include("dashboard.urls")),
    # Include our custom authentication URLs first
    path("accounts/", include("authentication.urls")),
    # Then include Django's built-in auth URLs (for any remaining URLs not covered by our custom ones)
    path("accounts/", include("django.contrib.auth.urls")),
    path("products/", include("products.urls")),
    path("suppliers/", include("suppliers.urls")),
    path("purchases/", include("purchases.urls")),
    path("sales/", include("sales.urls")),
    path("customers/", include("customers.urls")),
    path("expenses/", include("expenses.urls")),
    path("reports/", include("reports.urls")),
    path("notifications/", include("notifications.urls")),
    path("settings/", include("settings.urls")),
    path("superadmin/", include("superadmin.urls")),
    path("business-selection/", business_selection_view, name="business_selection"),
    # Django i18n set_language view (language switching)
    path("i18n/", include("django.conf.urls.i18n")),
]

# Serve media files in development and production
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files in development and production
# In production, WhiteNoise serves static files, but we also need this for direct access
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)