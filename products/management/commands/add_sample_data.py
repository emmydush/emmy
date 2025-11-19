from django.core.management.base import BaseCommand
from products.models import Product, Category, Unit
from superadmin.models import Business
from superadmin.middleware import set_current_business
import random


class Command(BaseCommand):
    help = "Add sample data to the inventory"

    def handle(self, *args, **options):
        # Get the specific business with ID 3
        business = Business.objects.get(id=3)
        self.stdout.write(f"Business: {business.company_name}")

        # Set the current business context
        set_current_business(business)

        # Get or create the Electronics category for this business
        category, created = Category.objects.get_or_create(
            business=business,
            name="Electronics",
            defaults={"description": "Electronic devices and accessories"},
        )
        if created:
            self.stdout.write(f"Created category: {category.name}")
        else:
            self.stdout.write(f"Using existing category: {category.name}")

        # Get or create the Piece unit
        unit, created = Unit.objects.get_or_create(
            business=business, name="Piece", defaults={"symbol": "pc"}
        )
        if created:
            self.stdout.write(f"Created unit: {unit.name}")
        else:
            self.stdout.write(f"Using existing unit: {unit.name}")

        # Product names and SKUs for variety
        product_names = [
            "Smartphone",
            "Laptop",
            "Tablet",
            "Smart Watch",
            "Bluetooth Headphones",
            "Wireless Earbuds",
            "Gaming Console",
            "Smart TV",
            "Digital Camera",
            "External Hard Drive",
            "USB Flash Drive",
            "Wireless Router",
            "Smart Speaker",
            "Fitness Tracker",
            "VR Headset",
            "Power Bank",
            "Bluetooth Speaker",
            "E-Reader",
            "Action Camera",
            "Gaming Mouse",
        ]

        skus = [
            "SP001",
            "LP002",
            "TB001",
            "SW001",
            "BH001",
            "WE001",
            "GC001",
            "ST001",
            "DC001",
            "EH001",
            "UF001",
            "WR001",
            "SS001",
            "FT001",
            "VR001",
            "PB001",
            "BS001",
            "ER001",
            "AC001",
            "GM001",
        ]

        # Create 20 products
        for i in range(20):
            name = product_names[i]
            sku = skus[i]

            # Generate random prices and quantities
            cost_price = round(random.uniform(50, 1000), 2)
            selling_price = round(cost_price * random.uniform(1.1, 1.5), 2)
            quantity = random.randint(5, 100)
            reorder_level = random.randint(1, 10)

            try:
                product = Product.objects.get(business=business, sku=sku)
                self.stdout.write(f"Product {product.name} already exists")
            except Product.DoesNotExist:
                product = Product(
                    business=business,
                    category=category,
                    unit=unit,
                    name=name,
                    sku=sku,
                    cost_price=cost_price,
                    selling_price=selling_price,
                    quantity=quantity,
                    reorder_level=reorder_level,
                )
                product.save()
                self.stdout.write(
                    f"Created product: {product.name} - SKU: {product.sku}, Quantity: {product.quantity}, Price: ${product.selling_price}"
                )

        # Show total products
        products = Product.objects.filter(business=business)
        self.stdout.write(
            f"Total products for {business.company_name}: {products.count()}"
        )

        # List all products
        self.stdout.write("All products:")
        for product in products:
            self.stdout.write(
                f"- {product.name}: {product.quantity} units, ${product.selling_price}"
            )
