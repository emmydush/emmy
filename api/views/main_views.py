from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone

from api.serializers.product_serializers import (
    ProductSerializer,
    ProductCreateUpdateSerializer,
    ProductListSerializer,
)
from api.serializers.sales_serializers import (
    SaleSerializer,
    SaleCreateUpdateSerializer,
    SaleListSerializer,
)
from products.models import Product
from sales.models import Sale


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "unit", "is_active"]
    search_fields = ["name", "sku", "barcode"]
    ordering_fields = ["name", "sku", "quantity", "selling_price"]
    ordering = ["name"]


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [IsAuthenticated]


class ProductUpdateView(generics.UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [IsAuthenticated]


class ProductDeleteView(generics.DestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class SaleListView(generics.ListAPIView):
    queryset = Sale.objects.all()
    serializer_class = SaleListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["customer", "payment_method", "is_refunded"]
    search_fields = ["id", "customer__full_name"]
    ordering_fields = ["sale_date", "total_amount"]
    ordering = ["-sale_date"]


class SaleDetailView(generics.RetrieveAPIView):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]


class SaleCreateView(generics.CreateAPIView):
    queryset = Sale.objects.all()
    serializer_class = SaleCreateUpdateSerializer
    permission_classes = [IsAuthenticated]


@api_view(["GET"])
@permission_classes([AllowAny])
def dashboard_stats(request):
    """
    Return dashboard statistics
    """
    # Filter low stock products using the is_low_stock property
    all_products = Product.objects.all()
    low_stock_count = sum(1 for product in all_products if product.is_low_stock)
    
    stats = {
        "total_products": Product.objects.count(),
        "low_stock_products": low_stock_count,
        "total_sales": Sale.objects.count(),
        "today_sales": Sale.objects.filter(
            sale_date__date=timezone.now().date()
        ).count(),
    }
    return Response(stats)
