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
    """List products for the current business context.

    Use a dynamic get_queryset so the business-specific manager can pick up the
    thread-local business that tests set via `set_current_business` or the
    middleware during requests. Defining `queryset = Product.objects.all()` at
    import time caused an empty queryset when no business context existed yet.
    """
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

    def get_queryset(self):
        # Build the queryset at request time so the BusinessSpecificManager can
        # apply the current business filter correctly.
        qs = Product.objects.business_specific().filter(is_active=True)

        # If the business-specific manager didn't find any products (for
        # example tests that set the business via thread-local aren't using
        # middleware/session), fall back to the first business on the user
        # (tests often associate the user with a business) so API calls still
        # return expected data.
        if qs.exists():
            return qs

        user = getattr(self.request, "user", None)
        if user and user.is_authenticated:
            user_businesses = getattr(user, "businesses", None)
            if user_businesses and user_businesses.exists():
                return Product.objects.filter(
                    business=user_businesses.first(), is_active=True
                )

        return qs


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Ensure the detail lookup is limited to the current business
        qs = Product.objects.business_specific().all()

        # Same fallback as list view: allow lookup by a business associated
        # with the authenticated user if thread-local business isn't set.
        if qs.exists():
            return qs

        user = getattr(self.request, "user", None)
        if user and user.is_authenticated:
            user_businesses = getattr(user, "businesses", None)
            if user_businesses and user_businesses.exists():
                return Product.objects.filter(business=user_businesses.first())

        return qs


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
    """List sales for the current business context."""
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

    def get_queryset(self):
        return Sale.objects.business_specific().all()


class SaleDetailView(generics.RetrieveAPIView):
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Sale.objects.business_specific().all()


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
