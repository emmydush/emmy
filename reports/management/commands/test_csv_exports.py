from django.core.management.base import BaseCommand
from django.test import RequestFactory
from authentication.models import User
from reports.views import (
    export_sales_report_csv,
    export_inventory_report_csv,
    export_profit_loss_report_csv,
    export_expenses_report_csv,
)
from superadmin.middleware import set_current_business
from superadmin.models import Business
from datetime import date, timedelta


class Command(BaseCommand):
    help = "Test that all report CSV exports work correctly"

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

        # Set date range
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        self.stdout.write(f"Testing CSV exports for business: {business.company_name}")
        self.stdout.write("=" * 50)

        # Test 1: Sales Report CSV Export
        self.stdout.write("Testing Sales Report CSV Export...")
        try:
            request = factory.get(
                f"/reports/sales/?export=csv&start_date={start_date}&end_date={end_date}"
            )
            request.user = user
            response = export_sales_report_csv(request, start_date, end_date)
            # Check if response is CSV
            if response["Content-Type"] == "text/csv":
                self.stdout.write(self.style.SUCCESS("✓ Sales Report CSV Export: OK"))
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "✗ Sales Report CSV Export: FAILED - Wrong content type"
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Sales Report CSV Export: FAILED - {str(e)}")
            )

        # Test 2: Inventory Report CSV Export
        self.stdout.write("Testing Inventory Report CSV Export...")
        try:
            request = factory.get("/reports/inventory/?export=csv")
            request.user = user
            response = export_inventory_report_csv(request)
            # Check if response is CSV
            if response["Content-Type"] == "text/csv":
                self.stdout.write(
                    self.style.SUCCESS("✓ Inventory Report CSV Export: OK")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "✗ Inventory Report CSV Export: FAILED - Wrong content type"
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Inventory Report CSV Export: FAILED - {str(e)}")
            )

        # Test 3: Profit & Loss Report CSV Export
        self.stdout.write("Testing Profit & Loss Report CSV Export...")
        try:
            request = factory.get(
                f"/reports/profit-loss/?export=csv&start_date={start_date}&end_date={end_date}"
            )
            request.user = user
            response = export_profit_loss_report_csv(request, start_date, end_date)
            # Check if response is CSV
            if response["Content-Type"] == "text/csv":
                self.stdout.write(
                    self.style.SUCCESS("✓ Profit & Loss Report CSV Export: OK")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "✗ Profit & Loss Report CSV Export: FAILED - Wrong content type"
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"✗ Profit & Loss Report CSV Export: FAILED - {str(e)}"
                )
            )

        # Test 4: Expenses Report CSV Export
        self.stdout.write("Testing Expenses Report CSV Export...")
        try:
            request = factory.get(
                f"/reports/expenses/?export=csv&start_date={start_date}&end_date={end_date}"
            )
            request.user = user
            response = export_expenses_report_csv(request, start_date, end_date)
            # Check if response is CSV
            if response["Content-Type"] == "text/csv":
                self.stdout.write(
                    self.style.SUCCESS("✓ Expenses Report CSV Export: OK")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "✗ Expenses Report CSV Export: FAILED - Wrong content type"
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Expenses Report CSV Export: FAILED - {str(e)}")
            )

        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS("CSV export testing completed!"))
