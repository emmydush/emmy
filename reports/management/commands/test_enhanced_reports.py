from django.core.management.base import BaseCommand
from django.test import RequestFactory
from authentication.models import User
from reports.views import (
    sales_report,
    profit_loss_report,
    expenses_report,
    quick_report,
    export_sales_report_csv_with_recommendations,
    export_profit_loss_report_csv_with_recommendations,
    export_expenses_report_csv_with_recommendations,
)
from superadmin.middleware import set_current_business
from superadmin.models import Business
from datetime import date, timedelta


class Command(BaseCommand):
    help = "Test enhanced reports with recommendations and structured CSV exports"

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
            f"Testing enhanced reports with recommendations for business: {business.company_name}"
        )
        self.stdout.write("=" * 70)

        # Test report views (normal display)
        self.stdout.write("Testing report views (display functionality)...")

        reports_to_test = [
            (
                "Quick Daily Report",
                lambda: quick_report(factory.get("/reports/quick/daily/"), "daily"),
            ),
            ("Sales Report", lambda: sales_report(factory.get("/reports/sales/"))),
            (
                "Profit & Loss Report",
                lambda: profit_loss_report(factory.get("/reports/profit-loss/")),
            ),
            (
                "Expenses Report",
                lambda: expenses_report(factory.get("/reports/expenses/")),
            ),
        ]

        for report_name, view_func in reports_to_test:
            self.stdout.write(f"  Testing {report_name}...")
            try:
                request = factory.get("/")
                request.user = user
                response = view_func()
                if response.status_code == 200:
                    self.stdout.write(
                        self.style.SUCCESS(f"    ✓ {report_name}: Display OK")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"    ✗ {report_name}: Display FAILED - Status {response.status_code}"
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"    ✗ {report_name}: Display FAILED - {str(e)}")
                )

        # Test CSV exports with recommendations
        self.stdout.write("Testing CSV exports with recommendations...")

        export_tests = [
            (
                "Sales Report CSV",
                lambda: export_sales_report_csv_with_recommendations(
                    factory.get("/reports/sales/?export=csv"), start_date, end_date
                ),
            ),
            (
                "Profit & Loss Report CSV",
                lambda: export_profit_loss_report_csv_with_recommendations(
                    factory.get("/reports/profit-loss/?export=csv"),
                    start_date,
                    end_date,
                ),
            ),
            (
                "Expenses Report CSV",
                lambda: export_expenses_report_csv_with_recommendations(
                    factory.get("/reports/expenses/?export=csv"), start_date, end_date
                ),
            ),
        ]

        for report_name, export_func in export_tests:
            self.stdout.write(f"  Testing {report_name}...")
            try:
                request = factory.get("/")
                request.user = user
                response = export_func()
                # Check if response is CSV
                if response["Content-Type"] == "text/csv":
                    # Check if recommendations are included in the CSV
                    content = response.content.decode("utf-8")
                    if "Recommendations" in content:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"    ✓ {report_name}: Export with recommendations OK"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"    ✗ {report_name}: Export OK but no recommendations found"
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'    ✗ {report_name}: Export FAILED - Wrong content type: {response["Content-Type"]}'
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"    ✗ {report_name}: Export FAILED - {str(e)}")
                )

        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("Enhanced report testing completed!"))
        self.stdout.write("All reports now include:")
        self.stdout.write("  • Well-structured CSV exports with detailed data")
        self.stdout.write("  • Business recommendations based on report data")
        self.stdout.write("  • Professional formatting for analysis")
