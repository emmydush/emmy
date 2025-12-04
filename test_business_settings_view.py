#!/usr/bin/env python
"""
Test script to simulate the business settings view and test updates.
"""

import os
import sys
import django
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages import get_messages

# Add the project directory to the Python path
sys.path.append("E:/AI")

# Set the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_management.settings")

# Setup Django
django.setup()

from authentication.models import User
from superadmin.models import Business
from settings.models import BusinessSettings
from settings.views import business_settings
from settings.forms import BusinessSettingsForm


def test_business_settings_view():
    """Test the business settings view functionality."""
    print("Testing business settings view...")

    # Find a business owner
    try:
        business_owner = User.objects.filter(owned_businesses__isnull=False).first()
        if not business_owner:
            print("No business owner found in the database.")
            return False

        business = business_owner.owned_businesses.first()
        print(f"Found business owner: {business_owner.username}")
        print(f"Business: {business.company_name}")

        # Create a request object
        factory = RequestFactory()
        request = factory.post(
            "/settings/business/",
            {
                "business_name": business.company_name,
                "business_address": "123 Test Street",
                "business_email": "test@example.com",
                "business_phone": "+1234567890",
                "currency": "USD",
                "currency_symbol": "$",
                "tax_rate": "10.5",
                "expiry_alert_days": "7",
                "near_expiry_alert_days": "30",
            },
        )

        # Add session and user to request
        from django.contrib.sessions.backends.db import SessionStore

        request.session = SessionStore()
        request.session["current_business_id"] = business.id
        request.user = business_owner

        # Add middleware to handle messages
        # Define a dummy get_response function for testing
        def dummy_get_response(request):
            return None

        middleware = SessionMiddleware(get_response=dummy_get_response)
        middleware.process_request(request)
        request.session.save()

        message_middleware = MessageMiddleware(get_response=dummy_get_response)
        message_middleware.process_request(request)

        # Call the view function
        response = business_settings(request)

        # Check if it was successful
        if response.status_code == 302:  # Redirect means success
            print("SUCCESS: Business settings view processed the update successfully!")

            # Verify the update in the database
            business_settings_obj = BusinessSettings.objects.get(business=business)
            if business_settings_obj.business_email == "test@example.com":
                print("SUCCESS: Business email was updated in the database!")
                return True
            else:
                print(
                    f"ERROR: Business email was not updated. Current value: {business_settings_obj.business_email}"
                )
                return False
        else:
            print(
                f"ERROR: View did not return redirect. Status code: {response.status_code}"
            )
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Business Settings View Test")
    print("=" * 40)

    success = test_business_settings_view()

    if success:
        print("\n✓ All tests passed! Business settings view works correctly.")
    else:
        print("\n✗ Tests failed! There may be issues with the business settings view.")

    sys.exit(0 if success else 1)
