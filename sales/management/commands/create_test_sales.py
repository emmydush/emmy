from django.core.management.base import BaseCommand
from sales.models import Sale, SaleItem
from products.models import Product
from customers.models import Customer
from decimal import Decimal
from django.utils import timezone


class Command(BaseCommand):
    help = "Create test sales data"

    def handle(self, *args, **options):
        # Get some products
        products = list(Product.objects.all()[:3])  # Get first 3 products

        if not products:
            self.stdout.write(
                self.style.ERROR("No products found. Please create products first.")
            )
            return

        # Create a customer for the sales
        customer, created = Customer.objects.get_or_create(
            email="test@example.com",
            defaults={
                "first_name": "Test",
                "last_name": "Customer",
                "phone": "+1234567890",
                "address": "123 Test Street",
                "company": "Test Company",
            },
        )

        if created:
            self.stdout.write(f"Created customer: {customer.full_name}")
        else:
            self.stdout.write(f"Using existing customer: {customer.full_name}")

        # Create sales
        sales_data = [
            {
                "customer": customer,
                "subtotal": Decimal("515.00"),
                "tax": Decimal("0.00"),
                "discount": Decimal("0.00"),
                "total_amount": Decimal("515.00"),
                "payment_method": "cash",
                "notes": "Test sale 1",
            },
            {
                "customer": customer,
                "subtotal": Decimal("30.00"),
                "tax": Decimal("0.00"),
                "discount": Decimal("0.00"),
                "total_amount": Decimal("30.00"),
                "payment_method": "credit_card",
                "notes": "Test sale 2",
            },
        ]

        sales = []
        for sale_data in sales_data:
            sale = Sale.objects.create(**sale_data)
            sales.append(sale)
            self.stdout.write(f"Created sale: {sale}")

        # Create sale items
        sale_items_data = [
            {
                "sale": sales[0],
                "product": products[0],  # Smartphone
                "quantity": Decimal("1"),
                "unit_price": products[0].selling_price,
                # total_price will be calculated automatically
            },
            {
                "sale": sales[0],
                "product": products[2],  # Coffee Beans
                "quantity": Decimal("1"),
                "unit_price": products[2].selling_price,
                # total_price will be calculated automatically
            },
            {
                "sale": sales[1],
                "product": products[1],  # T-Shirt
                "quantity": Decimal("2"),
                "unit_price": products[1].selling_price,
                # total_price will be calculated automatically
            },
        ]

        for item_data in sale_items_data:
            item = SaleItem.objects.create(**item_data)
            self.stdout.write(
                f"Created sale item: {item.quantity} x {item.product.name}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(sales)} sales with {len(sale_items_data)} items"
            )
        )
