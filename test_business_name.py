import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_management.settings")
django.setup()

from superadmin.models import Business
from settings.models import BusinessSettings

def test_business_name_display():
    print("Testing business name display logic...")
    
    # Create a test business
    business, created = Business.objects.get_or_create(
        company_name="Test Business Company",
        email="test@example.com",
        defaults={
            "business_type": "retail",
            "plan_type": "free",
            "status": "active"
        }
    )
    
    if created:
        print(f"Created test business: {business.company_name}")
    else:
        print(f"Using existing business: {business.company_name}")
    
    # Check if business settings exist for this business
    try:
        business_settings = BusinessSettings.objects.get(business=business)
        print(f"Found business settings: {business_settings.business_name}")
    except BusinessSettings.DoesNotExist:
        # Create business settings
        business_settings = BusinessSettings.objects.create(
            business=business,
            business_name=business.company_name,
            business_email=business.email
        )
        print(f"Created business settings: {business_settings.business_name}")
    
    # Test the context processor logic
    print("\nContext Processor Logic Test:")
    print(f"Business company name: {business.company_name}")
    print(f"Business settings name: {business_settings.business_name}")
    print(f"Should display: {business.company_name} (actual business name)")
    
    # Test global settings fallback
    print("\nGlobal Settings Fallback Test:")
    try:
        global_settings = BusinessSettings.objects.get(id=1)
        print(f"Global settings name: {global_settings.business_name}")
    except BusinessSettings.DoesNotExist:
        print("No global settings found")

if __name__ == "__main__":
    test_business_name_display()