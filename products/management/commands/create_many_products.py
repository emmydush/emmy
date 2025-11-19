from django.core.management.base import BaseCommand
from products.models import Product, Category, Unit
from superadmin.models import Business
from authentication.models import User
from decimal import Decimal
import random


class Command(BaseCommand):
    help = "Create many products for a specific user business"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            help="Email of the user to create products for",
            required=True,
        )
        parser.add_argument(
            "--count", type=int, help="Number of products to create", default=100
        )

    def handle(self, *args, **options):
        email = options["email"]
        count = options["count"]

        # Get the user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"User with email {email} does not exist")
            )
            return

        # Get the user's business
        try:
            business = Business.objects.get(owner=user)
        except Business.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No business found for user {email}"))
            return

        self.stdout.write(
            f"Creating {count} products for user {user.username} with business {business.company_name}"
        )

        # Get existing categories and units for this business
        categories = list(Category.objects.filter(business=business))
        units = list(Unit.objects.filter(business=business))

        # If no categories or units exist, create some
        if not categories:
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
                {
                    "name": "Beauty",
                    "description": "Cosmetics and personal care products",
                },
                {"name": "Sports", "description": "Sports equipment and accessories"},
                {"name": "Books", "description": "Books and educational materials"},
                {"name": "Toys", "description": "Toys and games for children"},
            ]

            for cat_data in categories_data:
                category, created = Category.objects.get_or_create(
                    business=business,
                    name=cat_data["name"],
                    defaults={"description": cat_data["description"]},
                )
                categories.append(category)

        if not units:
            units_data = [
                {"name": "Piece", "symbol": "pc"},
                {"name": "Kilogram", "symbol": "kg"},
                {"name": "Liter", "symbol": "L"},
                {"name": "Box", "symbol": "box"},
                {"name": "Pack", "symbol": "pack"},
                {"name": "Dozen", "symbol": "dz"},
            ]

            for unit_data in units_data:
                unit, created = Unit.objects.get_or_create(
                    business=business,
                    name=unit_data["name"],
                    defaults={"symbol": unit_data["symbol"]},
                )
                units.append(unit)

        # Product name templates
        product_prefixes = [
            "Premium",
            "Advanced",
            "Professional",
            "Deluxe",
            "Standard",
            "Basic",
            "Economy",
            "Luxury",
            "Classic",
            "Modern",
        ]

        product_names = [
            "Smartphone",
            "Laptop",
            "Tablet",
            "Headphones",
            "Speaker",
            "Camera",
            "Watch",
            "Fitness Tracker",
            "Gaming Console",
            "TV",
            "T-Shirt",
            "Jeans",
            "Jacket",
            "Dress",
            "Shoes",
            "Coffee",
            "Tea",
            "Juice",
            "Soda",
            "Water",
            "Tool Set",
            "Hammer",
            "Screwdriver",
            "Wrench",
            "Drill",
            "Shampoo",
            "Soap",
            "Lotion",
            "Perfume",
            "Makeup",
            "Football",
            "Basketball",
            "Tennis Racket",
            "Golf Club",
            "Yoga Mat",
            "Novel",
            "Textbook",
            "Magazine",
            "Comic",
            "Journal",
            "Toy Car",
            "Doll",
            "Puzzle",
            "Board Game",
            "Action Figure",
        ]

        product_suffixes = [
            "Pro",
            "Plus",
            "Max",
            "Mini",
            "Lite",
            "XL",
            "XXL",
            "Ultra",
            "Smart",
            "Digital",
        ]

        products_created = 0

        # Create products
        for i in range(count):
            # Generate a unique product name
            prefix = random.choice(product_prefixes)
            name = random.choice(product_names)
            suffix = random.choice(product_suffixes)
            product_name = f"{prefix} {name} {suffix}"

            # Generate SKU
            sku = f"SKU{random.randint(1000, 9999)}{chr(random.randint(65, 90))}"

            # Randomly select category and unit
            category = random.choice(categories)
            unit = random.choice(units)

            # Generate realistic prices
            cost_price = Decimal(str(round(random.uniform(5.0, 500.0), 2)))
            selling_price = Decimal(
                str(round(float(cost_price) * random.uniform(1.1, 3.0), 2))
            )

            # Generate quantity and reorder level
            quantity = Decimal(str(random.randint(0, 1000)))
            reorder_level = Decimal(str(random.randint(5, 50)))

            # Create product
            product, created = Product.objects.get_or_create(
                business=business,
                sku=sku,
                defaults={
                    "name": product_name,
                    "category": category,
                    "unit": unit,
                    "description": f"High-quality {product_name.lower()} suitable for everyday use",
                    "cost_price": cost_price,
                    "selling_price": selling_price,
                    "quantity": quantity,
                    "reorder_level": reorder_level,
                },
            )

            if created:
                products_created += 1
                self.stdout.write(
                    f"Created product: {product.name} (SKU: {product.sku})"
                )
            else:
                # If SKU already exists, try again with a different SKU
                sku = f"SKU{random.randint(10000, 99999)}{chr(random.randint(65, 90))}"
                product, created = Product.objects.get_or_create(
                    business=business,
                    sku=sku,
                    defaults={
                        "name": product_name,
                        "category": category,
                        "unit": unit,
                        "description": f"High-quality {product_name.lower()} suitable for everyday use",
                        "cost_price": cost_price,
                        "selling_price": selling_price,
                        "quantity": quantity,
                        "reorder_level": reorder_level,
                    },
                )
                if created:
                    products_created += 1
                    self.stdout.write(
                        f"Created product: {product.name} (SKU: {product.sku})"
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {products_created} products for user {email}"
            )
        )
