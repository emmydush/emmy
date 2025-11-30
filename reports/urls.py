from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.report_list, name="list"),
    path("quick/<str:period>/", views.quick_report, name="quick_report"),
    path("sales/", views.sales_report, name="sales"),
    path("inventory/", views.inventory_report, name="inventory"),
    path("profit-loss/", views.profit_loss_report, name="profit_loss"),
    path("expenses/", views.expenses_report, name="expenses"),
    path("multi-branch-dashboard/", views.multi_branch_dashboard, name="multi_branch_dashboard"),
    path(
        "test-charts/", views.test_charts, name="test_charts"
    ),  # Added test charts URL
]
