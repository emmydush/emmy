from django.core.management.base import BaseCommand
from django.test import RequestFactory
from authentication.models import User
from reports.views import (
    sales_report,
    inventory_report,
    profit_loss_report,
    expenses_report,
)
from superadmin.middleware import set_current_business
from superadmin.models import Business
import re


class Command(BaseCommand):
    help = "Test that all report templates have proper print functionality"

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

        self.stdout.write(
            f"Testing print functionality for reports in business: {business.company_name}"
        )
        self.stdout.write("=" * 60)

        # Test each report template for print functionality
        reports_to_test = [
            ("Sales Report", "/reports/sales/", sales_report, "reports/sales.html"),
            (
                "Inventory Report",
                "/reports/inventory/",
                inventory_report,
                "reports/inventory.html",
            ),
            (
                "Profit & Loss Report",
                "/reports/profit-loss/",
                profit_loss_report,
                "reports/profit_loss.html",
            ),
            (
                "Expenses Report",
                "/reports/expenses/",
                expenses_report,
                "reports/expenses.html",
            ),
        ]

        for report_name, url, view_func, template_name in reports_to_test:
            self.stdout.write(f"Testing {report_name}...")
            try:
                request = factory.get(url)
                request.user = user
                response = view_func(request)

                # Check if response contains the print button
                content = response.content.decode("utf-8")
                if "window.print()" in content or 'onclick="window.print()"' in content:
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ {report_name}: Print button found")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ {report_name}: Print button NOT found")
                    )

                # Check if response contains the export CSV button
                if "export=csv" in content:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ {report_name}: Export CSV button found"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ✗ {report_name}: Export CSV button NOT found"
                        )
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ {report_name}: FAILED - {str(e)}")
                )

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("Print functionality testing completed!"))
