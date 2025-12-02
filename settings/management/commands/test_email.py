from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from settings.utils import apply_email_settings

class Command(BaseCommand):
    help = "Test email functionality"

    def add_arguments(self, parser):
        parser.add_argument('--to', type=str, required=True, help='Recipient email address')
        parser.add_argument('--subject', type=str, default='Test Email', help='Email subject')
        parser.add_argument('--message', type=str, default='This is a test email.', help='Email message')

    def handle(self, *args, **options):
        self.stdout.write("Testing email functionality...")
        
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
        
        # Try to send a test email
        try:
            self.stdout.write(f"\nSending test email to {options['to']}...")
            send_mail(
                options['subject'],
                options['message'],
                settings.DEFAULT_FROM_EMAIL,
                [options['to']],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS("Email sent successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email: {e}"))
            # Print additional debugging info
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))