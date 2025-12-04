from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from settings.utils import apply_email_settings


class Command(BaseCommand):
    help = "Debug email functionality"

    def handle(self, *args, **options):
        self.stdout.write("Testing email functionality...")

        # Apply email settings from database
        self.stdout.write("Applying email settings...")
        apply_email_settings()

        # Print current email settings
        self.stdout.write("Current Django email settings:")
        self.stdout.write(
            f"  EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}"
        )
        self.stdout.write(f"  EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
        self.stdout.write(f"  EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
        self.stdout.write(
            f"  EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}"
        )
        self.stdout.write(
            f"  EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}"
        )
        self.stdout.write(
            f"  DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}"
        )

        # Try to send a test email
        try:
            self.stdout.write("\nSending test email...")
            send_mail(
                "Test Email",
                "This is a test email to verify email functionality.",
                "test@example.com",
                ["recipient@example.com"],
                fail_silently=False,  # Set to False to see errors
            )
            self.stdout.write(self.style.SUCCESS("Email sent successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email: {e}"))
