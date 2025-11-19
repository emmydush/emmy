from django.core.management.base import BaseCommand
from products.models import Category, Unit, Product
from suppliers.models import Supplier
from customers.models import Customer
from expenses.models import ExpenseCategory
from sales.models import Sale, SaleItem
from authentication.models import User
from decimal import Decimal
from django.utils import timezone
import random
from datetime import timedelta


class Command(BaseCommand):
    help = "Add sample data to reach approximately 70 entries"

    def handle(self, *args, **options):
        # Add more categories
        additional_categories = [
            {
                "name": "Sports & Outdoors",
                "description": "Sports equipment and outdoor gear",
            },
            {
                "name": "Beauty & Personal Care",
                "description": "Cosmetics and personal care items",
            },
            {"name": "Toys & Games", "description": "Toys for children and games"},
            {
                "name": "Automotive",
                "description": "Car accessories and automotive supplies",
            },
            {
                "name": "Health & Wellness",
                "description": "Health products and wellness items",
            },
            {
                "name": "Office Supplies",
                "description": "Office and stationery supplies",
            },
        ]

        categories = list(Category.objects.all())
        for cat_data in additional_categories:
            category, created = Category.objects.get_or_create(
                name=cat_data["name"], defaults=cat_data
            )
            categories.append(category)
            if created:
                self.stdout.write(f"Created category: {category.name}")

        # Add more units
        additional_units = [
            {"name": "Dozen", "symbol": "dz"},
            {"name": "Pair", "symbol": "pr"},
            {"name": "Meter", "symbol": "m"},
            {"name": "Milliliter", "symbol": "ml"},
        ]

        units = list(Unit.objects.all())
        for unit_data in additional_units:
            unit, created = Unit.objects.get_or_create(
                name=unit_data["name"], defaults={"symbol": unit_data["symbol"]}
            )
            units.append(unit)
            if created:
                self.stdout.write(f"Created unit: {unit.name} ({unit.symbol})")

        # Add more products (aiming for 50 total)
        existing_products = list(Product.objects.all())
        products_needed = 50 - len(existing_products)

        if products_needed > 0:
            product_names = [
                "Wireless Headphones",
                "Smart Watch",
                "Bluetooth Speaker",
                "Tablet",
                "Laptop",
                "Gaming Console",
                "Digital Camera",
                "Fitness Tracker",
                "Smart TV",
                "Printer",
                "Desk Lamp",
                "Office Chair",
                "Backpack",
                "Water Bottle",
                "Sunglasses",
                "Running Shoes",
                "Yoga Mat",
                "Dumbbells",
                "Tent",
                "Sleeping Bag",
                "Skincare Set",
                "Shampoo",
                "Body Lotion",
                "Perfume",
                "Makeup Kit",
                "Board Game",
                "Puzzle",
                "Action Figure",
                "Doll",
                "Toy Car",
                "Car Charger",
                "Phone Mount",
                "Tire Pressure Gauge",
                "Car Wax",
                "Air Freshener",
                "Vitamins",
                "Protein Powder",
                "Multivitamin",
                "Face Mask",
                "Hand Sanitizer",
                "Notebook",
                "Pen Set",
                "Stapler",
                "Paper Clips",
                "Binder",
                "Coffee Maker",
                "Blender",
                "Toaster",
                "Microwave",
                "Refrigerator",
            ]

            adjectives = [
                "Premium",
                "Deluxe",
                "Standard",
                "Basic",
                "Professional",
                "Advanced",
            ]
            materials = ["Steel", "Plastic", "Wood", "Glass", "Ceramic", "Fabric"]

            for i in range(products_needed):
                # Select random category and unit
                category = random.choice(categories)
                unit = random.choice(units)

                # Generate product name
                if i < len(product_names):
                    name = product_names[i]
                else:
                    adj = random.choice(adjectives)
                    material = random.choice(materials)
                    name = f"{adj} {material} Product {i+1}"

                # Generate SKU
                sku = f"SKU{i+5:03d}"  # Starting from SKU005 since we already have 4 products

                # Generate random prices and quantities
                cost_price = Decimal(random.randint(10, 500))
                selling_price = cost_price * Decimal(random.uniform(1.2, 2.5)).quantize(
                    Decimal("0.01")
                )
                quantity = Decimal(random.randint(5, 200))
                reorder_level = Decimal(random.randint(1, 20))

                product, created = Product.objects.get_or_create(
                    sku=sku,
                    defaults={
                        "name": name,
                        "category": category,
                        "unit": unit,
                        "description": f"High-quality {name.lower()} for everyday use",
                        "cost_price": cost_price,
                        "selling_price": selling_price,
                        "quantity": quantity,
                        "reorder_level": reorder_level,
                    },
                )

                if created:
                    self.stdout.write(
                        f"Created product: {product.name} (SKU: {product.sku})"
                    )
                    existing_products.append(product)

        # Add more suppliers (aiming for 10 total)
        existing_suppliers = list(Supplier.objects.all())
        suppliers_needed = 10 - len(existing_suppliers)

        if suppliers_needed > 0:
            supplier_names = [
                "Global Electronics Distributors",
                "Fashion World Ltd",
                "Food Services Inc",
                "Home Improvement Supplies",
                "Sports Gear Co",
                "Beauty Products LLC",
                "Toy Manufacturers Group",
                "Auto Parts Warehouse",
                "Health & Wellness Co",
                "Office Supply Central",
            ]

            supplier_domains = [
                "globalelectronics.com",
                "fashionworld.com",
                "foodservices.com",
                "homeimprovement.com",
                "sportsgear.com",
                "beautyproducts.com",
                "toymfg.com",
                "autoparts.com",
                "healthwellness.com",
                "officesupply.com",
            ]

            for i in range(suppliers_needed):
                if i < len(supplier_names):
                    name = supplier_names[i]
                    domain = supplier_domains[i]
                else:
                    name = f"Supplier Company {i+3}"  # Starting from 3 since we already have 2
                    domain = f"supplier{i+3}.com"

                supplier, created = Supplier.objects.get_or_create(
                    name=name,
                    defaults={
                        "email": f"info@{domain}",
                        "phone": f"+12345678{i+10:02d}",
                        "address": f"{i+100} Supplier Street, Business City, BC",
                        "company": name,
                        "contact_person": f"Contact Person {i+3}",
                        "contact_person_phone": f"+12345678{i+20:02d}",
                        "contact_person_email": f"contact@{domain}",
                    },
                )

                if created:
                    self.stdout.write(f"Created supplier: {supplier.name}")

        # Add more customers (aiming for 15 total)
        existing_customers = list(Customer.objects.all())
        customers_needed = 15 - len(existing_customers)

        if customers_needed > 0:
            first_names = [
                "James",
                "Mary",
                "John",
                "Patricia",
                "Robert",
                "Jennifer",
                "Michael",
                "Linda",
                "William",
                "Elizabeth",
                "David",
                "Barbara",
                "Richard",
                "Susan",
                "Joseph",
            ]

            last_names = [
                "Smith",
                "Johnson",
                "Williams",
                "Brown",
                "Jones",
                "Garcia",
                "Miller",
                "Davis",
                "Rodriguez",
                "Martinez",
                "Hernandez",
                "Lopez",
                "Gonzalez",
                "Wilson",
                "Anderson",
            ]

            for i in range(customers_needed):
                first_name = first_names[i % len(first_names)]
                last_name = last_names[i % len(last_names)]
                email = f"{first_name.lower()}.{last_name.lower()}{i+3}@example.com"  # Starting from 3 since we already have 2

                customer, created = Customer.objects.get_or_create(
                    email=email,
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "phone": f"+12345678{i+30:02d}",
                        "address": f"{i+200} Customer Avenue, Client Town, CT",
                        "company": f"{last_name} Enterprises" if i % 3 == 0 else "",
                    },
                )

                if created:
                    self.stdout.write(f"Created customer: {customer.full_name}")

        # Add more sales (aiming for 15 total)
        existing_sales = list(Sale.objects.all())
        sales_needed = 15 - len(existing_sales)

        if sales_needed > 0:
            # Get all customers and products
            all_customers = list(Customer.objects.all())
            all_products = list(Product.objects.all())

            if all_customers and all_products:
                payment_methods = [
                    "cash",
                    "credit_card",
                    "debit_card",
                    "mobile_payment",
                ]

                for i in range(sales_needed):
                    # Select random customer
                    customer = random.choice(all_customers)

                    # Select random products (1-5 products per sale)
                    num_products = random.randint(1, 5)
                    selected_products = random.sample(
                        all_products, min(num_products, len(all_products))
                    )

                    # Create sale
                    sale_date = timezone.now() - timedelta(days=random.randint(0, 30))
                    sale = Sale.objects.create(
                        customer=customer,
                        subtotal=Decimal("0.00"),
                        tax=Decimal("0.00"),
                        discount=Decimal("0.00"),
                        total_amount=Decimal("0.00"),
                        payment_method=random.choice(payment_methods),
                        notes=f"Test sale {len(existing_sales) + i + 1}",
                        created_at=sale_date,
                    )

                    # Create sale items
                    total_amount = Decimal("0.00")
                    for product in selected_products:
                        quantity = Decimal(random.randint(1, 3))
                        unit_price = product.selling_price
                        total_price = quantity * unit_price

                        SaleItem.objects.create(
                            sale=sale,
                            product=product,
                            quantity=quantity,
                            unit_price=unit_price,
                        )

                        total_amount += total_price

                    # Update sale totals
                    sale.subtotal = total_amount
                    sale.total_amount = total_amount
                    sale.save()

                    self.stdout.write(
                        f"Created sale: {sale} with {len(selected_products)} items"
                    )

        # Summary
        total_categories = Category.objects.count()
        total_units = Unit.objects.count()
        total_products = Product.objects.count()
        total_suppliers = Supplier.objects.count()
        total_customers = Customer.objects.count()
        total_sales = Sale.objects.count()
        total_sale_items = SaleItem.objects.count()
        total_users = User.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"\nData Summary:\n"
                f"Categories: {total_categories}\n"
                f"Units: {total_units}\n"
                f"Products: {total_products}\n"
                f"Suppliers: {total_suppliers}\n"
                f"Customers: {total_customers}\n"
                f"Sales: {total_sales}\n"
                f"Sale Items: {total_sale_items}\n"
                f"Users: {total_users}\n"
                f"Total Entries: {total_categories + total_units + total_products + total_suppliers + total_customers + total_sales + total_sale_items + total_users}"
            )
        )
