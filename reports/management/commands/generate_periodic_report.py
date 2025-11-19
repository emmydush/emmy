from django.core.management.base import BaseCommand
from django.test import RequestFactory
from authentication.models import User
from reports.views import sales_report, profit_loss_report, expenses_report
from superadmin.middleware import set_current_business
from superadmin.models import Business
from datetime import date, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = "Generate reports for different time periods: daily, weekly, monthly, yearly"

    def add_arguments(self, parser):
        parser.add_argument(
            "--period",
            type=str,
            choices=["daily", "weekly", "monthly", "yearly"],
            help="Time period for the report",
            required=True,
        )
        parser.add_argument(
            "--date",
            type=str,
            help="Specific date for the report (YYYY-MM-DD). Defaults to today.",
            required=False,
        )

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

        # Determine the date to use
        if options["date"]:
            try:
                report_date = date.fromisoformat(options["date"])
            except ValueError:
                self.stdout.write(
                    self.style.ERROR("Invalid date format. Use YYYY-MM-DD.")
                )
                return
        else:
            report_date = date.today()

        period = options["period"]

        self.stdout.write(
            f"Generating {period} report for {report_date} for business: {business.company_name}"
        )
        self.stdout.write("=" * 60)

        # Calculate date ranges based on period
        if period == "daily":
            start_date = report_date
            end_date = report_date
            period_name = f"{report_date}"
        elif period == "weekly":
            # Get the start of the week (Monday)
            start_date = report_date - timedelta(days=report_date.weekday())
            end_date = start_date + timedelta(days=6)
            period_name = f"Week of {start_date}"
        elif period == "monthly":
            # Get the first day of the month
            start_date = report_date.replace(day=1)
            # Get the last day of the month
            if report_date.month == 12:
                end_date = report_date.replace(day=31)
            else:
                # Get the first day of next month and subtract one day
                next_month = report_date.replace(day=1, month=report_date.month + 1)
                end_date = next_month - timedelta(days=1)
            period_name = f'{report_date.strftime("%B %Y")}'
        elif period == "yearly":
            # Get the first day of the year
            start_date = report_date.replace(month=1, day=1)
            # Get the last day of the year
            end_date = report_date.replace(month=12, day=31)
            period_name = f"{report_date.year}"

        self.stdout.write(f"Report period: {start_date} to {end_date}")

        # Test each report
        reports_to_test = [
            ("Sales Report", "/reports/sales/", sales_report),
            ("Profit & Loss Report", "/reports/profit-loss/", profit_loss_report),
            ("Expenses Report", "/reports/expenses/", expenses_report),
        ]

        for report_name, url, view_func in reports_to_test:
            self.stdout.write(f"  Generating {report_name}...")
            try:
                request = factory.get(
                    f"{url}?start_date={start_date}&end_date={end_date}"
                )
                request.user = user
                response = view_func(request)
                if response.status_code == 200:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    ✓ {report_name}: Generated successfully"
                        )
                    )
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

        self.stdout.write("=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"{period.capitalize()} report generation completed for {period_name}!"
            )
        )
