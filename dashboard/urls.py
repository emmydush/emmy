from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_view, name="index"),
    # Production dashboard views
    path("admin/", views.dashboard_view, name="admin"),
    path("manager/", views.dashboard_view, name="manager"),
    path("stock-manager/", views.dashboard_view, name="stock_manager"),
    path("cashier/", views.dashboard_view, name="cashier"),
    path("search/", views.search_view, name="search"),  # Add search URL
    path("switch-branch/", views.switch_branch_view, name="switch_branch"),  # Add branch switching URL
]