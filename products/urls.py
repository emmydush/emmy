from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('create/', views.product_create, name='create'),
    path('<int:pk>/', views.product_detail, name='detail'),
    path('<int:pk>/update/', views.product_update, name='update'),
    path('<int:pk>/delete/', views.product_delete, name='delete'),
    path('<int:pk>/json/', views.product_json, name='json'),
    path('bulk-upload/', views.bulk_upload, name='bulk_upload'),
    path('download-template/', views.download_template, name='download_template'),
    path('search/', views.product_search_ajax, name='search_ajax'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('units/', views.unit_list, name='unit_list'),
    path('units/create/', views.unit_create, name='unit_create'),
    path('stock-adjustments/', views.stock_adjustment_list, name='stock_adjustment_list'),
    path('stock-adjustments/request/', views.request_stock_adjustment, name='request_stock_adjustment'),
    path('stock-adjustments/<int:pk>/', views.stock_adjustment_detail, name='stock_adjustment_detail'),
    path('stock-adjustments/<int:pk>/approve/', views.approve_stock_adjustment, name='approve_stock_adjustment'),
    path('stock-alerts/', views.stock_alerts_list, name='stock_alerts_list'),
    path('stock-alerts/<int:pk>/resolve/', views.resolve_stock_alert, name='resolve_stock_alert'),
]