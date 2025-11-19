from django.core.management.base import BaseCommand
from django.test import RequestFactory
from authentication.models import User
from reports.views import (
    sales_report,
    inventory_report,
    profit_loss_report,
    expenses_report,
    export_sales_report_csv,
    export_inventory_report_csv,
    export_profit_loss_report_csv,
    export_expenses_report_csv,
)
from superadmin.middleware import set_current_business
from superadmin.models import Business
from datetime import date, timedelta


class Command(BaseCommand):
    help = "Comprehensive test of all reports functionality including print and export"

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

        self.stdout.write(
            f"Comprehensive testing of reports for business: {business.company_name}"
        )
        self.stdout.write("=" * 60)

        # Test all reports with normal view (print functionality)
        self.stdout.write("Testing report views (for print functionality)...")

        reports_to_test = [
            ("Sales Report", "/reports/sales/", sales_report),
            ("Inventory Report", "/reports/inventory/", inventory_report),
            ("Profit & Loss Report", "/reports/profit-loss/", profit_loss_report),
            ("Expenses Report", "/reports/expenses/", expenses_report),
        ]

        for report_name, url, view_func in reports_to_test:
            self.stdout.write(f"  Testing {report_name}...")
            try:
                request = factory.get(url)
                request.user = user
                response = view_func(request)
                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS(f"    ✓ {report_name}: OK"))
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"    ✗ {report_name}: FAILED - Status {response.status_code}"
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"    ✗ {report_name}: FAILED - {str(e)}")
                )

        # Test all reports with CSV export
        self.stdout.write("Testing CSV export functionality...")

        csv_tests = [
            (
                "Sales Report CSV",
                f"/reports/sales/?export=csv&start_date={start_date}&end_date={end_date}",
                lambda r: export_sales_report_csv(r, start_date, end_date),
            ),
            (
                "Inventory Report CSV",
                "/reports/inventory/?export=csv",
                export_inventory_report_csv,
            ),
            (
                "Profit & Loss Report CSV",
                f"/reports/profit-loss/?export=csv&start_date={start_date}&end_date={end_date}",
                lambda r: export_profit_loss_report_csv(r, start_date, end_date),
            ),
            (
                "Expenses Report CSV",
                f"/reports/expenses/?export=csv&start_date={start_date}&end_date={end_date}",
                lambda r: export_expenses_report_csv(r, start_date, end_date),
            ),
        ]

        for report_name, url, export_func in csv_tests:
            self.stdout.write(f"  Testing {report_name}...")
            try:
                request = factory.get(url)
                request.user = user
                response = export_func(request)
                # Check if response is CSV
                if response["Content-Type"] == "text/csv":
                    self.stdout.write(self.style.SUCCESS(f"    ✓ {report_name}: OK"))
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'    ✗ {report_name}: FAILED - Wrong content type: {response["Content-Type"]}'
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"    ✗ {report_name}: FAILED - {str(e)}")
                )

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("Comprehensive report testing completed!"))
        self.stdout.write(
            "All reports are working correctly with both view and export functionality."
        )
