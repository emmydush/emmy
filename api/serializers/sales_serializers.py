from rest_framework import serializers
from sales.models import Sale, SaleItem
from products.models import Product
from customers.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "sku", "selling_price"]


class SaleItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = SaleItem
        fields = "__all__"


class SaleSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    items = SaleItemSerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = "__all__"


class SaleCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = ["customer", "payment_method", "discount", "notes"]


class SaleListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)

    class Meta:
        model = Sale
        fields = [
            "id",
            "customer_name",
            "sale_date",
            "payment_method",
            "total_amount",
            "total_profit",
            "is_refunded",
        ]
