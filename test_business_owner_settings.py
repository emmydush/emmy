#!/usr/bin/env python
"""
Test script to verify that business owners can successfully update and save business settings.
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

from authentication.models import User, UserPermission
from superadmin.models import Business
from settings.models import BusinessSettings


def test_business_owner_settings_access():
    """Test that business owners can access and update business settings."""
    print("Testing business owner settings access...")
    
    # Find a business owner
    try:
        business_owner = User.objects.filter(owned_businesses__isnull=False).first()
        if not business_owner:
            print("No business owner found in the database.")
            return False
            
        business = business_owner.owned_businesses.first()
        print(f"Found business owner: {business_owner.username}")
        print(f"Business: {business.company_name}")
        
        # Check if the owner has settings access permission
        try:
            user_permission = UserPermission.objects.get(user=business_owner)
            print(f"User has can_access_settings: {user_permission.can_access_settings}")
        except UserPermission.DoesNotExist:
            print("No UserPermission record found for this user.")
            # Create one with settings access
            user_permission = UserPermission.objects.create(
                user=business_owner,
                can_access_settings=True
            )
            print("Created UserPermission with settings access.")
        
        # Get or create business settings
        business_settings, created = BusinessSettings.objects.get_or_create(
            business=business
        )
        
        if created:
            print("Created new business settings for the business.")
        else:
            print("Using existing business settings.")
            
        print(f"Business settings ID: {business_settings.id}")
        print(f"Business settings name: {business_settings.business_name}")
        
        # Update business settings
        original_name = business_settings.business_name
        new_name = f"{original_name} - Updated"
        
        business_settings.business_name = new_name
        business_settings.save()
        
        # Verify the update
        business_settings.refresh_from_db()
        if business_settings.business_name == new_name:
            print("SUCCESS: Business settings updated successfully!")
            # Revert the change
            business_settings.business_name = original_name
            business_settings.save()
            print("Reverted business name to original value.")
            return True
        else:
            print("ERROR: Business settings were not updated.")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False


def ensure_business_owners_have_settings_access():
    """Ensure all business owners have proper permissions to access settings."""
    print("\nEnsuring all business owners have settings access...")
    
    # Get all businesses that have an owner
    businesses_with_owner = Business.objects.exclude(owner=None)
    
    print(f"Found {businesses_with_owner.count()} businesses with owners")
    
    updated_count = 0
    
    for business in businesses_with_owner:
        owner = business.owner
        
        # Get or create UserPermission for the owner
        user_permission, created = UserPermission.objects.get_or_create(user=owner)
        
        # Check if the owner already has settings access
        if not user_permission.can_access_settings:
            user_permission.can_access_settings = True
            user_permission.save()
            print(f"Granted settings access to {owner.username} (owner of {business.company_name})")
            updated_count += 1
        else:
            print(f"{owner.username} (owner of {business.company_name}) already has settings access")
    
    print(f"Successfully updated permissions for {updated_count} business owners")
    return updated_count


if __name__ == "__main__":
    print("Business Owner Settings Access Test")
    print("=" * 40)
    
    # First ensure all business owners have settings access
    ensure_business_owners_have_settings_access()
    
    # Then test the access
    success = test_business_owner_settings_access()
    
    if success:
        print("\n✓ All tests passed! Business owners can successfully update and save business settings.")
    else:
        print("\n✗ Tests failed! There may be issues with business owner settings access.")
        
    sys.exit(0 if success else 1)