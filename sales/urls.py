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
    path("pos/quagga-test/", views.quagga_test_view, name="quagga_test"),
    path(
        "pos/quagga-test-simple/",
        views.quagga_test_simple_view,
        name="quagga_test_simple",
    ),
    path(
        "product/<int:product_id>/",
        views.get_product_details,
        name="get_product_details",
    ),
    path(
        "product/variant/<int:variant_id>/",
        views.get_product_variant_details,
        name="get_product_variant_details",
    ),
    # Barcode scanning endpoint
    path(
        "product/barcode/<str:barcode>/",
        views.get_product_by_barcode,
        name="get_product_by_barcode",
    ),
    path("credit-sales/", views.credit_sales_list, name="credit_sales_list"),
    path("credit-sales/create/", views.credit_sale_create, name="credit_sale_create"),
    path("credit-sales/<int:pk>/", views.credit_sale_detail, name="credit_sale_detail"),
    path(
        "credit-sales/<int:pk>/payments/",
        views.credit_payment_create,
        name="credit_sale_payments",
    ),
    path(
        "credit-sales/add-payment/<int:sale_id>/",
        views.credit_payment_create,
        name="add_credit_payment",
    ),
    path(
        "credit-sales/overdue/", views.overdue_credit_sales, name="overdue_credit_sales"
    ),
]
