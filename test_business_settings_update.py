#!/usr/bin/env python
"""
Test script to verify that business settings can be updated successfully.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append("E:/AI")

# Set the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_management.settings")

# Setup Django
django.setup()

from authentication.models import User
from superadmin.models import Business
from settings.models import BusinessSettings
from settings.forms import BusinessSettingsForm


def test_business_settings_update():
    """Test that business settings can be updated successfully."""
    print("Testing business settings update...")

    # Find a business owner
    try:
        business_owner = User.objects.filter(owned_businesses__isnull=False).first()
        if not business_owner:
            print("No business owner found in the database.")
            return False

        business = business_owner.owned_businesses.first()
        print(f"Found business owner: {business_owner.username}")
        print(f"Business: {business.company_name}")

        # Get or create business settings
        business_settings, created = BusinessSettings.objects.get_or_create(
            business=business
        )

        if created:
            print("Created new business settings for the business.")
        else:
            print("Using existing business settings.")

        print(f"Business settings ID: {business_settings.id}")
        print(f"Original business email: {business_settings.business_email}")

        # Test updating business settings using the form
        original_email = business_settings.business_email
        new_email = "updated@example.com"

        # Create form data
        form_data = {
            "business_name": business_settings.business_name,
            "business_address": business_settings.business_address,
            "business_email": new_email,
            "business_phone": business_settings.business_phone,
            "currency": business_settings.currency,
            "currency_symbol": business_settings.currency_symbol,
            "tax_rate": business_settings.tax_rate,
            "expiry_alert_days": business_settings.expiry_alert_days,
            "near_expiry_alert_days": business_settings.near_expiry_alert_days,
        }

        # Create and validate form
        form = BusinessSettingsForm(data=form_data, instance=business_settings)

        if form.is_valid():
            print("Form is valid, saving...")
            form.save()

            # Verify the update
            business_settings.refresh_from_db()
            if business_settings.business_email == new_email:
                print("SUCCESS: Business settings updated successfully!")
                # Revert the change
                business_settings.business_email = original_email
                business_settings.save()
                print("Reverted business email to original value.")
                return True
            else:
                print("ERROR: Business settings were not updated.")
                print(f"Expected: {new_email}, Got: {business_settings.business_email}")
                return False
        else:
            print("ERROR: Form is not valid!")
            print("Form errors:", form.errors)
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Business Settings Update Test")
    print("=" * 40)

    success = test_business_settings_update()

    if success:
        print("\n✓ All tests passed! Business settings can be successfully updated.")
    else:
        print("\n✗ Tests failed! There may be issues with business settings updates.")

    sys.exit(0 if success else 1)
