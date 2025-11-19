from django.core.management.base import BaseCommand
from sales.models import Sale, SaleItem
from products.models import Product
from customers.models import Customer
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import random


class Command(BaseCommand):
    help = "Create 100 sample sales records with related data"

    def handle(self, *args, **options):
        # First, ensure we have some products
        products = list(Product.objects.business_specific())
        if not products:
            self.stdout.write(
                self.style.ERROR(
                    'No products found. Please create products first using "python manage.py create_test_data"'
                )
            )
            return

        # Ensure we have some customers
        customers = list(Customer.objects.business_specific())
        if not customers:
            # Create sample customers
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
                    email=f"{first_name.lower()}.{last_name.lower()}@example.com",
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "phone": f"+1-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                        "address": f'{random.randint(100, 999)} {random.choice(["Main", "Oak", "Pine", "Elm", "Maple"])} St, City {i+1}',
                        "company": f'{last_name} {random.choice(["Corp", "LLC", "Inc", "Ltd"])}',
                    },
                )
                if created:
                    self.stdout.write(f"Created customer: {customer.full_name}")
                customers.append(customer)

        # Create 100 sales
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

            # Create sale
            sale = Sale.objects.create(
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
                f"Successfully created {sales_created} sales with {sale_items_created} sale items"
            )
        )
