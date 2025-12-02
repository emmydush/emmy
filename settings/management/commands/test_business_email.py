from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from settings.models import BusinessSettings
from settings.utils import apply_email_settings
from superadmin.models import Business
from authentication.models import User

class Command(BaseCommand):
    help = "Test business registration email functionality"

    def add_arguments(self, parser):
        parser.add_argument('--to', type=str, required=True, help='Recipient email address')
        parser.add_argument('--business-name', type=str, default='Test Business', help='Business name for the test')
        parser.add_argument('--username', type=str, default='testuser', help='Username for the test')

    def handle(self, *args, **options):
        self.stdout.write("Testing business registration email functionality...")
        
        # Apply email settings from database
        self.stdout.write("Applying email settings from database...")
        apply_email_settings()
        
        # Print current email settings
        self.stdout.write("Current Django email settings:")
        self.stdout.write(f"  EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
        self.stdout.write(f"  EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
        self.stdout.write(f"  EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
        self.stdout.write(f"  EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
        self.stdout.write(f"  EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
        self.stdout.write(f"  DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
        
        # Create mock business and user objects for testing
        self.stdout.write("\nCreating mock business and user for testing...")
        
        # Create a mock user
        owner = User()
        owner.username = options['username']
        owner.email = options['to']
        
        # Create a mock business
        business = Business()
        business.company_name = options['business_name']
        business.email = options['to']
        business.owner = owner
        
        # Get business settings
        try:
            business_settings = BusinessSettings.objects.get(business=business)
        except BusinessSettings.DoesNotExist:
            try:
                business_settings = BusinessSettings.objects.get(id=1)
            except BusinessSettings.DoesNotExist:
                business_settings = BusinessSettings.objects.create(
                    id=1,
                    business_name="Smart Solution",
                    business_address="123 Business Street, City, Country",
                    business_email="info@smartsolution.com",
                    business_phone="+1 (555) 123-4567",
                    currency="FRW",
                    currency_symbol="FRW",
                    tax_rate=0,
                )
        
        # Prepare email context
        context = {
            "business": business,
            "business_settings": business_settings,
            "owner": owner,
            "login_url": "http://localhost:8000/accounts/login/",
            "current_year": timezone.now().year,
        }
        
        # Try to send a test email using the business registration template
        try:
            self.stdout.write(f"\nSending business registration email to {options['to']}...")
            
            # Import template rendering functions
            from django.template.loader import render_to_string
            
            # Render email templates
            subject = f"[{business_settings.business_name}] Business Registration Confirmation"
            html_message = render_to_string("emails/business_registration.html", context)
            plain_message = render_to_string("emails/business_registration.txt", context)
            
            # Send email
            send_mail(
                subject,
                plain_message,
                business_settings.business_email or settings.DEFAULT_FROM_EMAIL,
                [options['to']],
                html_message=html_message,
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS("Business registration email sent successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send business registration email: {e}"))
            # Print additional debugging info
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))