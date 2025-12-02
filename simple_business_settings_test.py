#!/usr/bin/env python
"""
Simple test script to verify business settings update functionality.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('E:/AI')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_management.settings')

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
        
        # Get business settings
        try:
            business_settings = BusinessSettings.objects.get(business=business)
            print(f"Found business settings (ID: {business_settings.id})")
        except BusinessSettings.DoesNotExist:
            print("No business settings found, creating new ones...")
            business_settings = BusinessSettings.objects.create(business=business)
            print(f"Created business settings (ID: {business_settings.id})")
            
        # Save original values
        original_email = business_settings.business_email
        original_name = business_settings.business_name
        print(f"Original email: {original_email}")
        print(f"Original name: {original_name}")
        
        # Test updating with new values
        new_email = "test-update@example.com"
        new_name = f"{original_name} - Updated"
        
        print(f"Updating to email: {new_email}")
        print(f"Updating to name: {new_name}")
        
        # Update directly through the model
        business_settings.business_email = new_email
        business_settings.business_name = new_name
        business_settings.save()
        
        # Verify the update
        business_settings.refresh_from_db()
        
        if business_settings.business_email == new_email and business_settings.business_name == new_name:
            print("SUCCESS: Business settings updated successfully through model!")
            
            # Test updating through form
            form_data = {
                'business_name': original_name,
                'business_address': business_settings.business_address,
                'business_email': original_email,
                'business_phone': business_settings.business_phone,
                'currency': business_settings.currency,
                'currency_symbol': business_settings.currency_symbol,
                'tax_rate': business_settings.tax_rate,
                'expiry_alert_days': business_settings.expiry_alert_days,
                'near_expiry_alert_days': business_settings.near_expiry_alert_days,
            }
            
            form = BusinessSettingsForm(data=form_data, instance=business_settings)
            if form.is_valid():
                form.save()
                print("SUCCESS: Business settings updated successfully through form!")
                
                # Verify the revert
                business_settings.refresh_from_db()
                if business_settings.business_email == original_email and business_settings.business_name == original_name:
                    print("SUCCESS: Business settings reverted successfully!")
                    return True
                else:
                    print("ERROR: Business settings were not reverted properly.")
                    return False
            else:
                print("ERROR: Form is not valid!")
                print("Form errors:", form.errors)
                return False
        else:
            print("ERROR: Business settings were not updated through model.")
            print(f"Expected email: {new_email}, Got: {business_settings.business_email}")
            print(f"Expected name: {new_name}, Got: {business_settings.business_name}")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Simple Business Settings Test")
    print("=" * 40)
    
    success = test_business_settings_update()
    
    if success:
        print("\n✓ All tests passed! Business settings can be successfully updated and saved.")
    else:
        print("\n✗ Tests failed! There may be issues with business settings updates.")
        
    sys.exit(0 if success else 1)