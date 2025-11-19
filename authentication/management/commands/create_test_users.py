from django.core.management.base import BaseCommand
from authentication.models import User


class Command(BaseCommand):
    help = "Create test users for development"

    def handle(self, *args, **options):
        # Create admin user
        if not User.objects.filter(username="admin").exists():
            User.objects.create_user(
                username="admin",
                email="admin@example.com",
                password="admin123",
                first_name="Admin",
                last_name="User",
                role="admin",
            )
            self.stdout.write(self.style.SUCCESS("Successfully created admin user"))

        # Create manager user
        if not User.objects.filter(username="manager").exists():
            User.objects.create_user(
                username="manager",
                email="manager@example.com",
                password="manager123",
                first_name="Manager",
                last_name="User",
                role="manager",
            )
            self.stdout.write(self.style.SUCCESS("Successfully created manager user"))

        # Create cashier user
        if not User.objects.filter(username="cashier").exists():
            User.objects.create_user(
                username="cashier",
                email="cashier@example.com",
                password="cashier123",
                first_name="Cashier",
                last_name="User",
                role="cashier",
            )
            self.stdout.write(self.style.SUCCESS("Successfully created cashier user"))

        # Create stock manager user
        if not User.objects.filter(username="stockmanager").exists():
            User.objects.create_user(
                username="stockmanager",
                email="stockmanager@example.com",
                password="stockmanager123",
                first_name="Stock",
                last_name="Manager",
                role="stock_manager",
            )
            self.stdout.write(
                self.style.SUCCESS("Successfully created stock manager user")
            )

        self.stdout.write(self.style.SUCCESS("All test users created successfully!"))
