from django.urls import path
from . import views

app_name = "expenses"

urlpatterns = [
    path("", views.expense_list, name="list"),
    path("create/", views.expense_create, name="create"),
    path("<int:pk>/", views.expense_detail, name="detail"),
    path("<int:pk>/update/", views.expense_update, name="update"),
    path("<int:pk>/delete/", views.expense_delete, name="delete"),
    path("categories/", views.category_list, name="category_list"),
    path("categories/create/", views.category_create, name="category_create"),
]
