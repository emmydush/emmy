import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_management.settings")
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from settings.models import EmailSettings
from settings.utils import apply_email_settings


def test_email_function():
    print("Testing email function...")

    # Apply email settings from database
    print("Applying email settings...")
    apply_email_settings()

    # Print current email settings
    print("Current Django email settings:")
    print(f"  EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
    print(f"  EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
    print(f"  EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
    print(f"  EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
    print(f"  EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
    print(f"  DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")

    # Try to send a test email
    try:
        print("\nSending test email...")
        send_mail(
            "Test Email",
            "This is a test email to verify email functionality.",
            "test@example.com",
            ["recipient@example.com"],
            fail_silently=False,  # Set to False to see errors
        )
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


if __name__ == "__main__":
    test_email_function()
