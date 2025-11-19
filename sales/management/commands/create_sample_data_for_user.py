from django.core.management.base import BaseCommand
from sales.models import Sale, SaleItem
from products.models import Product
from customers.models import Customer
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import random
from superadmin.models import Business
from authentication.models import User


class Command(BaseCommand):
    help = "Create 100 sample sales records for a specific user"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            help="Email of the user to create data for",
            required=True,
        )

    def handle(self, *args, **options):
        email = options["email"]

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
            f"Creating data for user {user.username} with business {business.company_name}"
        )

        # Set the business context (this is a simplified approach)
        # In a real multi-tenancy setup, we would use middleware to set the context
        # For this command, we'll directly associate objects with the business

        # First, ensure we have some products for this business
        products = list(Product.objects.filter(business=business))
        if not products:
            # Create sample products for this business
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

            units_data = [
                {"name": "Piece", "symbol": "pc"},
                {"name": "Kilogram", "symbol": "kg"},
                {"name": "Liter", "symbol": "L"},
                {"name": "Box", "symbol": "box"},
            ]

            # Create categories for this business
            from products.models import Category, Unit

            categories = []
            for cat_data in categories_data:
                category, created = Category.objects.get_or_create(
                    business=business,
                    name=cat_data["name"],
                    defaults={"description": cat_data["description"]},
                )
                categories.append(category)

            # Create units for this business
            units = []
            for unit_data in units_data:
                unit, created = Unit.objects.get_or_create(
                    business=business,
                    name=unit_data["name"],
                    defaults={"symbol": unit_data["symbol"]},
                )
                units.append(unit)

            # Create products for this business
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
                    business=business, sku=product_data["sku"], defaults=product_data
                )
                products.append(product)

        # Ensure we have some customers for this business
        customers = list(Customer.objects.filter(business=business))
        if not customers:
            # Create sample customers for this business
            customer_names = [
                ("John", "Doe"),
                ("Jane", "Smith"),
                ("Robert", "Johnson"),
                ("Emily", "Williams"),
                ("Michael", "Brown"),
                ("Sarah", "Davis"),
                ("David", "Miller"),
                ("Lisa", "Wilson"),
                ("James", "Moore"),
                ("Jennifer", "Taylor"),
                ("William", "Anderson"),
                ("Patricia", "Thomas"),
                ("Richard", "Jackson"),
                ("Linda", "White"),
                ("Charles", "Harris"),
                ("Barbara", "Martin"),
                ("Joseph", "Thompson"),
                ("Elizabeth", "Garcia"),
                ("Thomas", "Martinez"),
                ("Susan", "Robinson"),
            ]

            for i, (first_name, last_name) in enumerate(customer_names):
                customer, created = Customer.objects.get_or_create(
                    business=business,
                    email=f"{first_name.lower()}.{last_name.lower()}@example.com",
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "phone": f"+1-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                        "address": f'{random.randint(100, 999)} {random.choice(["Main", "Oak", "Pine", "Elm", "Maple"])} St, City {i+1}',
                        "company": f'{last_name} {random.choice(["Corp", "LLC", "Inc", "Ltd"])}',
                    },
                )
                customers.append(customer)

        # Create 100 sales for this business
        sales_created = 0
        sale_items_created = 0

        for i in range(100):
            # Randomly select a customer
            customer = random.choice(customers)

            # Random date within the last 30 days
            random_days = random.randint(0, 30)
            sale_date = timezone.now() - timedelta(days=random_days)

            # Random payment method
            payment_methods = ["cash", "credit_card", "mobile_money", "bank_transfer"]
            payment_method = random.choice(payment_methods)

            # Create sale for this business
            sale = Sale.objects.create(
                business=business,
                customer=customer,
                sale_date=sale_date,
                subtotal=Decimal("0"),
                tax=Decimal("0"),
                discount=Decimal("0"),
                total_amount=Decimal("0"),
                payment_method=payment_method,
                notes=f"Sample sale #{i+1}",
            )
            sales_created += 1

            # Create random number of sale items (1-5 items per sale)
            num_items = random.randint(1, 5)
            sale_subtotal = Decimal("0")

            for j in range(num_items):
                # Randomly select a product
                product = random.choice(products)

                # Random quantity (1-10)
                quantity = Decimal(str(random.randint(1, 10)))

                # Use product's selling price
                unit_price = product.selling_price

                # Create sale item
                sale_item = SaleItem.objects.create(
                    sale=sale, product=product, quantity=quantity, unit_price=unit_price
                )
                sale_items_created += 1

                # Add to sale subtotal
                sale_subtotal += sale_item.total_price

            # Update sale with calculated totals
            sale.subtotal = sale_subtotal
            sale.total_amount = (
                sale_subtotal  # Not including tax/discount in this sample
            )
            sale.save()

            self.stdout.write(f"Created sale #{i+1} with {num_items} items")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {sales_created} sales with {sale_items_created} sale items for user {email}"
            )
        )
