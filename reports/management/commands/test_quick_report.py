from django.core.management.base import BaseCommand
from django.test import RequestFactory
from authentication.models import User
from reports.views import quick_report
from superadmin.middleware import set_current_business
from superadmin.models import Business


class Command(BaseCommand):
    help = "Test the quick report view functionality"

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
            f"Testing quick report view for business: {business.company_name}"
        )
        self.stdout.write("=" * 60)

        # Test each period
        periods = ["daily", "weekly", "monthly", "yearly"]

        for period in periods:
            self.stdout.write(f"Testing {period} quick report...")
            try:
                request = factory.get(f"/reports/quick/{period}/")
                request.user = user
                response = quick_report(request, period)
                if response.status_code == 200:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ {period.capitalize()} quick report: OK"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ✗ {period.capitalize()} quick report: FAILED - Status {response.status_code}"
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ {period.capitalize()} quick report: FAILED - {str(e)}"
                    )
                )

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("Quick report view testing completed!"))
