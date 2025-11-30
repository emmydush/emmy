from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from settings.models import EmailSettings, BusinessSettings


class Command(BaseCommand):
    help = "Test the current email configuration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--recipient", type=str, help="Email address to send test email to"
        )

    def handle(self, *args, **options):
        # Get email settings
        try:
            email_settings = EmailSettings.objects.get(id=1)
        except EmailSettings.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    "Email settings not configured. Please configure email settings first."
                )
            )
            return

        # Get recipient email
        recipient_email = options["recipient"]
        if not recipient_email:
            # Try to get from business settings
            try:
                # Try to get business-specific settings first
                business_settings = BusinessSettings.objects.exclude(business__isnull=True).first()
                if not business_settings:
                    # Fall back to global settings
                    business_settings = BusinessSettings.objects.get(id=1)
                recipient_email = business_settings.business_email
            except:
                self.stdout.write(
                    self.style.ERROR(
                        "No recipient email provided and no business email configured."
                    )
                )
                return

        # Print current email settings
        self.stdout.write("\nCurrent Django email settings:")
        self.stdout.write(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
        self.stdout.write(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
        self.stdout.write(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
        self.stdout.write(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
        self.stdout.write(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
        self.stdout.write(f"EMAIL_USE_SSL: {getattr(settings, 'EMAIL_USE_SSL', 'Not set')}")
        self.stdout.write(
            f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}"
        )

        # Check if database email settings exist
        try:
            email_settings = EmailSettings.objects.get(id=1)
            self.stdout.write("\nDatabase email settings found:")
            self.stdout.write(f"Email Backend: {email_settings.email_backend}")
            self.stdout.write(f"Email Host: {email_settings.email_host}")
            self.stdout.write(f"Email Port: {email_settings.email_port}")
            self.stdout.write(f"Email Host User: {email_settings.email_host_user}")
            self.stdout.write(f"Use TLS: {email_settings.email_use_tls}")
            self.stdout.write(f"Use SSL: {email_settings.email_use_ssl}")
            self.stdout.write(f"Default From Email: {email_settings.default_from_email}")

            # Apply database email settings
            self.stdout.write("\nApplying database email settings...")
            from settings.utils import apply_email_settings
            apply_email_settings()

            self.stdout.write("\nEmail settings after applying database settings:")
            self.stdout.write(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
            self.stdout.write(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
            self.stdout.write(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
            self.stdout.write(
                f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}"
            )
            self.stdout.write(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
            self.stdout.write(f"EMAIL_USE_SSL: {getattr(settings, 'EMAIL_USE_SSL', 'Not set')}")
            self.stdout.write(
                f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}"
            )

        except EmailSettings.DoesNotExist:
            self.stdout.write("\nNo database email settings found. Using default settings.")

        # Test sending a simple email
        self.stdout.write(f"\nTesting email sending to {recipient_email}...")
        try:
            send_mail(
                "Test Email Configuration",
                "This is a test email to verify that your email configuration is working correctly.",
                settings.DEFAULT_FROM_EMAIL,
                [recipient_email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS("✓ Email sent successfully! Check your inbox."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Failed to send email: {str(e)}"))