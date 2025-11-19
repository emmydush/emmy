from django.core.management.base import BaseCommand
from django.test import Client
from authentication.models import User
from superadmin.models import Business
import re


class Command(BaseCommand):
    help = "Test web interface for enhanced reports with recommendations"

    def handle(self, *args, **options):
        # Create a test client
        client = Client()

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

        self.stdout.write(
            f"Testing web interface for enhanced reports for business: {business.company_name}"
        )
        self.stdout.write("=" * 70)

        # Log in the user
        client.force_login(user)

        # Test quick report page
        self.stdout.write("Testing quick report page...")
        try:
            response = client.get("/reports/quick/daily/")
            if response.status_code == 200:
                content = response.content.decode("utf-8")
                if "Recommendations" in content:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "  ✓ Quick Daily Report: Page loads with recommendations"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            "  ⚠ Quick Daily Report: Page loads but no recommendations section"
                        )
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ Quick Daily Report: FAILED - Status {response.status_code}"
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ✗ Quick Daily Report: FAILED - {str(e)}")
            )

        # Test sales report page
        self.stdout.write("Testing sales report page...")
        try:
            response = client.get("/reports/sales/")
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS("  ✓ Sales Report: Page loads"))
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ Sales Report: FAILED - Status {response.status_code}"
                    )
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Sales Report: FAILED - {str(e)}"))

        # Test CSV export with recommendations
        self.stdout.write("Testing CSV export with recommendations...")
        try:
            response = client.get("/reports/quick/daily/?export=csv")
            if response.status_code == 200 and response["Content-Type"] == "text/csv":
                content = response.content.decode("utf-8")
                # Check if CSV has proper structure
                lines = content.split("\n")
                has_recommendations = any("Recommendations" in line for line in lines)
                has_structured_data = any(
                    "Summary" in line or "Metric" in line for line in lines
                )

                if has_recommendations and has_structured_data:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "  ✓ Quick Report CSV: Well-structured with recommendations"
                        )
                    )
                elif has_structured_data:
                    self.stdout.write(
                        self.style.WARNING(
                            "  ⚠ Quick Report CSV: Structured but no recommendations section"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            "  ⚠ Quick Report CSV: May not be properly structured"
                        )
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ Quick Report CSV: FAILED - Status {response.status_code} or wrong content type"
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ✗ Quick Report CSV: FAILED - {str(e)}")
            )

        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("Web interface testing completed!"))
