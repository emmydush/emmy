from django.urls import path, include
from api.views.main_views import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    SaleListView,
    SaleDetailView,
    SaleCreateView,
    dashboard_stats,
)
from api.views.auth_views import (
    LoginView,
    LogoutView,
    RegisterView,
    UserProfileView,
    PasswordChangeView,
)
from api.views.docs_views import APIDocumentationView

app_name = "api"

urlpatterns = [
    # API Documentation
    path("", APIDocumentationView.as_view(), name="api_docs"),
    # Authentication
    path("auth/login/", LoginView.as_view(), name="api_login"),
    path("auth/logout/", LogoutView.as_view(), name="api_logout"),
    path("auth/register/", RegisterView.as_view(), name="api_register"),
    path("auth/profile/", UserProfileView.as_view(), name="api_profile"),
    path(
        "auth/password/change/",
        PasswordChangeView.as_view(),
        name="api_password_change",
    ),
    # Products
    path("products/", ProductListView.as_view(), name="api_product_list"),
    path("products/create/", ProductCreateView.as_view(), name="api_product_create"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="api_product_detail"),
    path(
        "products/<int:pk>/update/",
        ProductUpdateView.as_view(),
        name="api_product_update",
    ),
    path(
        "products/<int:pk>/delete/",
        ProductDeleteView.as_view(),
        name="api_product_delete",
    ),
    # Sales
    path("sales/", SaleListView.as_view(), name="api_sale_list"),
    path("sales/create/", SaleCreateView.as_view(), name="api_sale_create"),
    path("sales/<int:pk>/", SaleDetailView.as_view(), name="api_sale_detail"),
    # Dashboard
    path("dashboard/stats/", dashboard_stats, name="api_dashboard_stats"),
]
