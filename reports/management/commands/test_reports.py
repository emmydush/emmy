from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from authentication.models import User
from reports.views import (
    sales_report,
    inventory_report,
    profit_loss_report,
    expenses_report,
)
from superadmin.middleware import set_current_business
from superadmin.models import Business


class Command(BaseCommand):
    help = "Test that all reports work correctly"

    def handle(self, *args, **options):
        # Create a request factory
        factory = RequestFactory()

        # Get a user
        try:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR("No users found"))
                return
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("No users found"))
            return

        # Get a business
        try:
            business = Business.objects.first()
            if not business:
                self.stdout.write(self.style.ERROR("No businesses found"))
                return
        except Business.DoesNotExist:
            self.stdout.write(self.style.ERROR("No businesses found"))
            return

        # Set business context
        set_current_business(business)

        self.stdout.write(f"Testing reports for business: {business.company_name}")
        self.stdout.write("=" * 50)

        # Test 1: Sales Report
        self.stdout.write("Testing Sales Report...")
        try:
            request = factory.get("/reports/sales/")
            request.user = user
            response = sales_report(request)
            self.stdout.write(self.style.SUCCESS("✓ Sales Report: OK"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Sales Report: FAILED - {str(e)}"))

        # Test 2: Inventory Report
        self.stdout.write("Testing Inventory Report...")
        try:
            request = factory.get("/reports/inventory/")
            request.user = user
            response = inventory_report(request)
            self.stdout.write(self.style.SUCCESS("✓ Inventory Report: OK"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Inventory Report: FAILED - {str(e)}")
            )

        # Test 3: Profit & Loss Report
        self.stdout.write("Testing Profit & Loss Report...")
        try:
            request = factory.get("/reports/profit-loss/")
            request.user = user
            response = profit_loss_report(request)
            self.stdout.write(self.style.SUCCESS("✓ Profit & Loss Report: OK"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Profit & Loss Report: FAILED - {str(e)}")
            )

        # Test 4: Expenses Report
        self.stdout.write("Testing Expenses Report...")
        try:
            request = factory.get("/reports/expenses/")
            request.user = user
            response = expenses_report(request)
            self.stdout.write(self.style.SUCCESS("✓ Expenses Report: OK"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Expenses Report: FAILED - {str(e)}"))

        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS("Report testing completed!"))
