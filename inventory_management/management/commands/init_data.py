from django.core.management.base import BaseCommand
from authentication.models import User
from products.models import Category, Unit, Product
from suppliers.models import Supplier
from customers.models import Customer
from expenses.models import ExpenseCategory


class Command(BaseCommand):
    help = "Initialize database with sample data"

    def handle(self, *args, **options):
        # Create superuser if it doesn't exist
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                email="admin@example.com",
                password="admin123",
                first_name="Admin",
                last_name="User",
                role="admin",
            )
            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully created superuser "admin" with password "admin123"'
                )
            )

        # Create sample categories
        categories_data = [
            {
                "name": "Electronics",
                "description": "Electronic devices and accessories",
            },
            {"name": "Clothing", "description": "Apparel and fashion items"},
            {"name": "Food & Beverages", "description": "Food products and beverages"},
            {
                "name": "Home & Garden",
                "description": "Home improvement and garden supplies",
            },
            {"name": "Books", "description": "Books and educational materials"},
        ]

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data["name"], defaults=cat_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created category: {category.name}")
                )

        # Create sample units
        units_data = [
            {"name": "Piece", "symbol": "pcs"},
            {"name": "Kilogram", "symbol": "kg"},
            {"name": "Gram", "symbol": "g"},
            {"name": "Liter", "symbol": "L"},
            {"name": "Box", "symbol": "box"},
            {"name": "Pack", "symbol": "pack"},
        ]

        for unit_data in units_data:
            unit, created = Unit.objects.get_or_create(
                name=unit_data["name"], defaults={"symbol": unit_data["symbol"]}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created unit: {unit.name} ({unit.symbol})")
                )

        # Create sample suppliers
        suppliers_data = [
            {
                "name": "Tech Solutions Inc.",
                "email": "info@techsolutions.com",
                "phone": "+1234567890",
                "address": "123 Tech Street, Silicon Valley, CA",
                "company": "Tech Solutions Inc.",
                "contact_person": "John Smith",
                "contact_person_phone": "+1234567891",
                "contact_person_email": "john@techsolutions.com",
            },
            {
                "name": "Global Food Suppliers",
                "email": "orders@globalfood.com",
                "phone": "+1234567892",
                "address": "456 Food Avenue, New York, NY",
                "company": "Global Food Suppliers",
                "contact_person": "Maria Garcia",
                "contact_person_phone": "+1234567893",
                "contact_person_email": "maria@globalfood.com",
            },
        ]

        for supplier_data in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                name=supplier_data["name"], defaults=supplier_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created supplier: {supplier.name}")
                )

        # Create sample customers
        customers_data = [
            {
                "first_name": "Robert",
                "last_name": "Johnson",
                "email": "robert@example.com",
                "phone": "+1234567894",
                "address": "789 Customer Lane, Los Angeles, CA",
                "company": "Johnson Enterprises",
            },
            {
                "first_name": "Sarah",
                "last_name": "Williams",
                "email": "sarah@example.com",
                "phone": "+1234567895",
                "address": "321 Client Road, Chicago, IL",
            },
        ]

        for customer_data in customers_data:
            customer, created = Customer.objects.get_or_create(
                email=customer_data["email"], defaults=customer_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created customer: {customer.full_name}")
                )

        # Create sample expense categories
        expense_categories_data = [
            {"name": "Rent", "description": "Monthly rent payment"},
            {"name": "Utilities", "description": "Electricity, water, internet bills"},
            {"name": "Salaries", "description": "Employee salaries and wages"},
            {
                "name": "Marketing",
                "description": "Advertising and promotional expenses",
            },
            {
                "name": "Maintenance",
                "description": "Equipment and facility maintenance",
            },
        ]

        for category_data in expense_categories_data:
            category, created = ExpenseCategory.objects.get_or_create(
                name=category_data["name"], defaults=category_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created expense category: {category.name}")
                )

        self.stdout.write(
            self.style.SUCCESS("Successfully initialized database with sample data")
        )
