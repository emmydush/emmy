from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.product_list, name="list"),
    path("create/", views.product_create, name="create"),
    path("<int:pk>/", views.product_detail, name="detail"),
    path("<int:pk>/update/", views.product_update, name="update"),
    path("<int:pk>/delete/", views.product_delete, name="delete"),
    path("<int:pk>/json/", views.product_json, name="json"),
    path("bulk-upload/", views.bulk_upload, name="bulk_upload"),
    path("download-template/", views.download_template, name="download_template"),
    path("search/", views.product_search_ajax, name="search_ajax"),
    # Variant management URLs
    path("<int:product_pk>/variants/", views.product_variant_list, name="variant_list"),
    path(
        "<int:product_pk>/variants/create/",
        views.product_variant_create,
        name="variant_create",
    ),
    path("variants/<int:pk>/", views.product_variant_detail, name="variant_detail"),
    path(
        "variants/<int:pk>/update/", views.product_variant_update, name="variant_update"
    ),
    path(
        "variants/<int:pk>/delete/", views.product_variant_delete, name="variant_delete"
    ),
    # Variant attribute management URLs
    path("attributes/", views.variant_attribute_list, name="variant_attribute_list"),
    path(
        "attributes/create/",
        views.variant_attribute_create,
        name="variant_attribute_create",
    ),
    path(
        "attributes/<int:pk>/update/",
        views.variant_attribute_update,
        name="variant_attribute_update",
    ),
    path(
        "attributes/<int:pk>/delete/",
        views.variant_attribute_delete,
        name="variant_attribute_delete",
    ),
    # Variant attribute value management URLs
    path(
        "attribute-values/",
        views.variant_attribute_value_list,
        name="variant_attribute_value_list",
    ),
    path(
        "attribute-values/create/",
        views.variant_attribute_value_create,
        name="variant_attribute_value_create",
    ),
    path(
        "attribute-values/<int:pk>/update/",
        views.variant_attribute_value_update,
        name="variant_attribute_value_update",
    ),
    path(
        "attribute-values/<int:pk>/delete/",
        views.variant_attribute_value_delete,
        name="variant_attribute_value_delete",
    ),
    # Inventory transfer URLs
    path("transfers/", views.inventory_transfer_list, name="inventory_transfer_list"),
    path(
        "transfers/create/",
        views.inventory_transfer_create,
        name="inventory_transfer_create",
    ),
    path(
        "transfers/<int:pk>/",
        views.inventory_transfer_detail,
        name="inventory_transfer_detail",
    ),
    path(
        "transfers/<int:pk>/update/",
        views.inventory_transfer_update,
        name="inventory_transfer_update",
    ),
    path(
        "transfers/<int:pk>/complete/",
        views.inventory_transfer_complete,
        name="inventory_transfer_complete",
    ),
    path(
        "transfers/<int:pk>/cancel/",
        views.inventory_transfer_cancel,
        name="inventory_transfer_cancel",
    ),
    path("categories/", views.category_list, name="category_list"),
    path("categories/create/", views.category_create, name="category_create"),
    path("categories/<int:pk>/update/", views.category_update, name="category_update"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    path("units/", views.unit_list, name="unit_list"),
    path("units/create/", views.unit_create, name="unit_create"),
    path(
        "stock-adjustments/", views.stock_adjustment_list, name="stock_adjustment_list"
    ),
    path(
        "stock-adjustments/request/",
        views.request_stock_adjustment,
        name="request_stock_adjustment",
    ),
    path(
        "stock-adjustments/<int:pk>/",
        views.stock_adjustment_detail,
        name="stock_adjustment_detail",
    ),
    path(
        "stock-adjustments/<int:pk>/approve/",
        views.approve_stock_adjustment,
        name="approve_stock_adjustment",
    ),
    path("stock-alerts/", views.stock_alerts_list, name="stock_alerts_list"),
    path(
        "stock-alerts/<int:pk>/resolve/",
        views.resolve_stock_alert,
        name="resolve_stock_alert",
    ),
]
