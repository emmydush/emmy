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

print("Fixing role and permissions for user 'royke'...")
try:
    # Get the user
    user = User.objects.get(username='royke')
    print(f"Found user: {user.username}")
    print(f"Current role: '{user.role}'")
    
    # Set the role to admin
    user.role = 'admin'
    user.save()
    print("Updated user role to 'admin'")
    
    # Check if user has a business
    if not user.owned_businesses.exists():
        print("User does not own any businesses")
    else:
        business = user.owned_businesses.first()
        print(f"User owns business: {business.company_name}")
        
        # Ensure business is active
        if business.status != "active":
            business.status = "active"
            business.save()
            print(f"Activated business: {business.company_name}")
    
    # Associate user with their business if not already associated
    if user.owned_businesses.exists():
        business = user.owned_businesses.first()
        if not user.businesses.filter(id=business.id).exists():
            user.businesses.add(business)
            print(f"Associated user with business: {business.company_name}")
    
    # Create or update UserPermission
    user_permission, created = UserPermission.objects.get_or_create(user=user)
    
    # Set all permissions to True for business owners
    user_permission.can_create = True
    user_permission.can_edit = True
    user_permission.can_delete = True
    user_permission.can_manage_users = True
    user_permission.can_create_users = True
    user_permission.can_edit_users = True
    user_permission.can_delete_users = True
    user_permission.can_access_products = True
    user_permission.can_access_sales = True
    user_permission.can_access_purchases = True
    user_permission.can_access_customers = True
    user_permission.can_access_suppliers = True
    user_permission.can_access_expenses = True
    user_permission.can_access_reports = True
    user_permission.can_access_settings = True
    
    user_permission.save()
    
    if created:
        print("Created new UserPermission record with full access")
    else:
        print("Updated existing UserPermission record with full access")
        
    print(f"Successfully fixed role and permissions for user: {user.username}")
    print("User should now be able to access the platform as a business owner.")
    
except User.DoesNotExist:
    print("User with username 'royke' does not exist")
except Exception as e:
    print(f"Error fixing role and permissions: {str(e)}")