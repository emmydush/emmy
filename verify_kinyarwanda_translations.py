#!/usr/bin/env python
"""
Test script to verify Kinyarwanda translations are working in templates
"""
import os
import sys
import django
import uuid

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_management.settings")
django.setup()

# Add 'testserver' to ALLOWED_HOSTS for testing
from django.conf import settings

settings.ALLOWED_HOSTS.append("testserver")

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import translation


def test_kinyarwanda_translations():
    """Test that Kinyarwanda translations work correctly"""
    User = get_user_model()

    # Generate a unique username for each test run
    unique_id = str(uuid.uuid4())[:8]
    username = f"testuser_{unique_id}"

    # Create a test user
    user = User.objects.create_user(
        username=username,
        email=f"test{unique_id}@example.com",
        password="testpass123",
        language="rw",  # Set language to Kinyarwanda
    )

    # Create a test client
    client = Client()

    # Log in the user
    login_success = client.login(username=username, password="testpass123")
    if not login_success:
        print("❌ Failed to log in test user")
        return False

    # Activate Kinyarwanda translations
    translation.activate("rw")

    # Test that the login page shows Kinyarwanda translations
    response = client.get(reverse("authentication:login"))

    # Check for Kinyarwanda translations in the response
    content = response.content.decode("utf-8")

    # Check for some key Kinyarwanda translations
    expected_translations = [
        "Injira",  # Signin
        "Izina nkomoko",  # Username
        "Ijambo ry'ibanga",  # Password
    ]

    missing_translations = []
    for trans in expected_translations:
        if trans not in content:
            missing_translations.append(trans)

    if missing_translations:
        print(f"❌ Missing Kinyarwanda translations: {missing_translations}")
        print("Content preview:")
        print(content[:1000])  # Print first 1000 characters for debugging
        return False
    else:
        print("✅ All expected Kinyarwanda translations found in login page!")

    # Test dashboard page
    response = client.get(reverse("dashboard:index"))
    content = response.content.decode("utf-8")

    # Check for some key Kinyarwanda translations in dashboard
    expected_dashboard_translations = [
        "Ahantu",  # Home
        "Ibicuruzwa",  # Products
        "Ibyiciro",  # Categories
    ]

    missing_translations = []
    for trans in expected_dashboard_translations:
        if trans not in content:
            missing_translations.append(trans)

    if missing_translations:
        print(
            f"❌ Missing Kinyarwanda translations in dashboard: {missing_translations}"
        )
        return False
    else:
        print("✅ All expected Kinyarwanda translations found in dashboard!")

    print("✅ All Kinyarwanda translation tests passed!")
    return True


if __name__ == "__main__":
    test_kinyarwanda_translations()
