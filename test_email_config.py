#!/usr/bin/env python
"""
Test script to verify email configuration works correctly.
This script tests both the database email settings and the local settings.
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_management.settings")
django.setup()

from django.core.mail import send_mail
from django.conf import settings as django_settings
from settings.models import EmailSettings
from settings.utils import apply_email_settings


def test_email_config():
    print("Testing email configuration...")

    # Print current email settings
    print("\nCurrent Django email settings:")
    print(f"EMAIL_BACKEND: {getattr(django_settings, 'EMAIL_BACKEND', 'Not set')}")
    print(f"EMAIL_HOST: {getattr(django_settings, 'EMAIL_HOST', 'Not set')}")
    print(f"EMAIL_PORT: {getattr(django_settings, 'EMAIL_PORT', 'Not set')}")
    print(f"EMAIL_HOST_USER: {getattr(django_settings, 'EMAIL_HOST_USER', 'Not set')}")
    print(f"EMAIL_USE_TLS: {getattr(django_settings, 'EMAIL_USE_TLS', 'Not set')}")
    print(f"EMAIL_USE_SSL: {getattr(django_settings, 'EMAIL_USE_SSL', 'Not set')}")
    print(
        f"DEFAULT_FROM_EMAIL: {getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'Not set')}"
    )

    # Check if database email settings exist
    try:
        email_settings = EmailSettings.objects.get(id=1)
        print("\nDatabase email settings found:")
        print(f"Email Backend: {email_settings.email_backend}")
        print(f"Email Host: {email_settings.email_host}")
        print(f"Email Port: {email_settings.email_port}")
        print(f"Email Host User: {email_settings.email_host_user}")
        print(f"Use TLS: {email_settings.email_use_tls}")
        print(f"Use SSL: {email_settings.email_use_ssl}")
        print(f"Default From Email: {email_settings.default_from_email}")

        # Apply database email settings
        print("\nApplying database email settings...")
        apply_email_settings()

        print("\nEmail settings after applying database settings:")
        print(f"EMAIL_BACKEND: {getattr(django_settings, 'EMAIL_BACKEND', 'Not set')}")
        print(f"EMAIL_HOST: {getattr(django_settings, 'EMAIL_HOST', 'Not set')}")
        print(f"EMAIL_PORT: {getattr(django_settings, 'EMAIL_PORT', 'Not set')}")
        print(
            f"EMAIL_HOST_USER: {getattr(django_settings, 'EMAIL_HOST_USER', 'Not set')}"
        )
        print(f"EMAIL_USE_TLS: {getattr(django_settings, 'EMAIL_USE_TLS', 'Not set')}")
        print(f"EMAIL_USE_SSL: {getattr(django_settings, 'EMAIL_USE_SSL', 'Not set')}")
        print(
            f"DEFAULT_FROM_EMAIL: {getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'Not set')}"
        )

    except EmailSettings.DoesNotExist:
        print("\nNo database email settings found. Using default settings.")

    # Test sending a simple email
    print("\nTesting email sending...")
    try:
        send_mail(
            "Test Email Configuration",
            "This is a test email to verify that your email configuration is working correctly.",
            django_settings.DEFAULT_FROM_EMAIL,
            ["test@example.com"],
            fail_silently=False,
        )
        print("✓ Email sent successfully! Check your console or email inbox.")
    except Exception as e:
        print(f"✗ Failed to send email: {str(e)}")


if __name__ == "__main__":
    test_email_config()
