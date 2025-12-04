from django.core.management.base import BaseCommand
from superadmin.models import Business
from settings.models import BusinessSettings


class Command(BaseCommand):
    help = "Initialize business-specific settings for all existing businesses"

    def handle(self, *args, **options):
        # Get the global business settings as template
        try:
            global_settings = BusinessSettings.objects.get(id=1)
        except BusinessSettings.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    "Global business settings not found. Please run 'python manage.py init_business_settings' first."
                )
            )
            return

        # Get all businesses that don't have settings yet
        businesses_without_settings = Business.objects.filter(settings__isnull=True)

        if not businesses_without_settings.exists():
            self.stdout.write(
                self.style.SUCCESS("All businesses already have their own settings.")
            )
            return

        created_count = 0
        for business in businesses_without_settings:
            # Create business-specific settings
            BusinessSettings.objects.create(
                business=business,
                business_name=global_settings.business_name,
                business_address=global_settings.business_address,
                business_email=global_settings.business_email,
                business_phone=global_settings.business_phone,
                business_logo=global_settings.business_logo,
                currency=global_settings.currency,
                currency_symbol=global_settings.currency_symbol,
                tax_rate=global_settings.tax_rate,
                expiry_alert_days=global_settings.expiry_alert_days,
                near_expiry_alert_days=global_settings.near_expiry_alert_days,
            )
            created_count += 1
            self.stdout.write(f"Created settings for business: {business.company_name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created settings for {created_count} businesses."
            )
        )
