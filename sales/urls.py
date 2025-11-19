from django.urls import path
from . import views
from . import cart_views

app_name = "sales"

urlpatterns = [
    path("", views.sale_list, name="list"),
    path("create/", views.sale_create, name="create"),
    path("<int:pk>/", views.sale_detail, name="detail"),
    path("<int:pk>/update/", views.sale_update, name="update"),
    path("<int:pk>/delete/", views.sale_delete, name="delete"),
    path("<int:pk>/refund/", views.sale_refund, name="refund"),
    path("pos/", views.pos_view, name="pos"),
    path("pos/process/", views.process_pos_sale, name="process_pos_sale"),
    path("pos/test-scanner/", views.test_scanner_view, name="test_scanner"),
    path("pos/scanner-test/", views.pos_scanner_test_view, name="pos_scanner_test"),
    path("pos/camera-test/", views.camera_test_view, name="camera_test"),
    path(
        "pos/automatic-scanner-test/",
        views.automatic_scanner_test_view,
        name="automatic_scanner_test",
    ),
    path(
        "pos/simple-camera-test/",
        views.simple_camera_test_view,
        name="simple_camera_test",
    ),
    path(
        "pos/scanner-diagnostics/",
        views.scanner_diagnostics_view,
        name="scanner_diagnostics",
    ),
    path("pos/scanner-debug/", views.scanner_debug_view, name="scanner_debug"),
    path(
        "product/<int:product_id>/",
        views.get_product_details,
        name="get_product_details",
    ),
    path(
        "product/barcode/<str:barcode>/",
        views.get_product_by_barcode,
        name="get_product_by_barcode",
    ),
    # New cart URLs
    path("cart/add/", cart_views.add_to_cart, name="add_to_cart"),
    path("cart/update/", cart_views.update_cart_item, name="update_cart_item"),
    path("cart/remove/", cart_views.remove_from_cart, name="remove_from_cart"),
    path("cart/get/", cart_views.get_cart, name="get_cart"),
    path("cart/clear/", cart_views.clear_cart, name="clear_cart"),
    path(
        "cart/process/",
        cart_views.process_sale_from_cart,
        name="process_sale_from_cart",
    ),
]
