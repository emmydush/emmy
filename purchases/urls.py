from django.urls import path
from . import views

app_name = "purchases"

urlpatterns = [
    path("", views.purchase_order_list, name="list"),
    path("create/", views.purchase_order_create, name="create"),
    path("<int:pk>/", views.purchase_order_detail, name="detail"),
    path("<int:pk>/update/", views.purchase_order_update, name="update"),
    path("<int:pk>/delete/", views.purchase_order_delete, name="delete"),
    path("<int:pk>/receive/", views.receive_items, name="receive_items"),
]
