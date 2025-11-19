from django.core.management.base import BaseCommand
from products.models import Category, Unit, Product
from decimal import Decimal


class Command(BaseCommand):
    help = "Create test data for products, categories, and units"

    def handle(self, *args, **options):
        # Create categories
        categories_data = [
            {
                "name": "Electronics",
                "description": "Electronic devices and accessories",
            },
            {"name": "Clothing", "description": "Apparel and fashion items"},
            {"name": "Food & Beverages", "description": "Food products and drinks"},
            {
                "name": "Home & Garden",
                "description": "Home improvement and garden supplies",
            },
        ]

        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data["name"], defaults={"description": cat_data["description"]}
            )
            categories.append(category)
            if created:
                self.stdout.write(f"Created category: {category.name}")
            else:
                self.stdout.write(f"Category already exists: {category.name}")

        # Create units
        units_data = [
            {"name": "Piece", "symbol": "pc"},
            {"name": "Kilogram", "symbol": "kg"},
            {"name": "Liter", "symbol": "L"},
            {"name": "Box", "symbol": "box"},
        ]

        units = []
        for unit_data in units_data:
            unit, created = Unit.objects.get_or_create(
                name=unit_data["name"], defaults={"symbol": unit_data["symbol"]}
            )
            units.append(unit)
            if created:
                self.stdout.write(f"Created unit: {unit.name}")
            else:
                self.stdout.write(f"Unit already exists: {unit.name}")

        # Create products
        products_data = [
            {
                "name": "Smartphone",
                "sku": "SP001",
                "category": categories[0],
                "unit": units[0],
                "description": "Latest model smartphone with advanced features",
                "cost_price": Decimal("300.00"),
                "selling_price": Decimal("500.00"),
                "quantity": Decimal("50"),
                "reorder_level": Decimal("10"),
            },
            {
                "name": "T-Shirt",
                "sku": "TS001",
                "category": categories[1],
                "unit": units[0],
                "description": "Cotton t-shirt in various colors",
                "cost_price": Decimal("5.00"),
                "selling_price": Decimal("15.00"),
                "quantity": Decimal("200"),
                "reorder_level": Decimal("50"),
            },
            {
                "name": "Coffee Beans",
                "sku": "CB001",
                "category": categories[2],
                "unit": units[2],
                "description": "Premium roasted coffee beans",
                "cost_price": Decimal("8.00"),
                "selling_price": Decimal("15.00"),
                "quantity": Decimal("30"),
                "reorder_level": Decimal("10"),
            },
            {
                "name": "Garden Tools Set",
                "sku": "GT001",
                "category": categories[3],
                "unit": units[3],
                "description": "Complete set of garden tools",
                "cost_price": Decimal("25.00"),
                "selling_price": Decimal("45.00"),
                "quantity": Decimal("25"),
                "reorder_level": Decimal("5"),
            },
        ]

        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                sku=product_data["sku"], defaults=product_data
            )
            if created:
                self.stdout.write(f"Created product: {product.name}")
            else:
                self.stdout.write(f"Product already exists: {product.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(categories)} categories, {len(units)} units, and {len(products_data)} products"
            )
        )
