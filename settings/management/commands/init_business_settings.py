from django.core.management.base import BaseCommand
from settings.models import BusinessSettings

class Command(BaseCommand):
    help = 'Initialize default business settings'

    def handle(self, *args, **options):
        # Check if BusinessSettings with id=1 already exists
        if BusinessSettings.objects.filter(id=1).exists():
            self.stdout.write(
                self.style.SUCCESS('Business settings already exist')
            )
            return

        # Create default business settings
        business_settings = BusinessSettings.objects.create(
            id=1,
            business_name='Smart Solution',
            business_address='123 Business Street, City, Country',
            business_email='info@smartsolution.com',
            business_phone='+1 (555) 123-4567',
            currency='FRW',
            currency_symbol='FRW',
            tax_rate=0
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created business settings: {business_settings.business_name}')
        )