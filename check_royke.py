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

print("Checking user 'royke'...")
try:
    user = User.objects.get(username='royke')
    print(f"User found: {user.username}")
    print(f"Role: {user.role}")
    print(f"Email: {user.email}")
    
    # Check owned businesses
    owned_businesses = user.owned_businesses.all()
    print(f"Owned businesses: {owned_businesses.count()}")
    for business in owned_businesses:
        print(f"  - {business.company_name} (status: {business.status})")
        
    # Check associated businesses
    associated_businesses = user.businesses.all()
    print(f"Associated businesses: {associated_businesses.count()}")
    for business in associated_businesses:
        print(f"  - {business.company_name} (status: {business.status})")
        
    # Check user permissions
    try:
        user_permission = UserPermission.objects.get(user=user)
        print("User permissions found:")
        print(f"  - can_create: {user_permission.can_create}")
        print(f"  - can_edit: {user_permission.can_edit}")
        print(f"  - can_delete: {user_permission.can_delete}")
        print(f"  - can_manage_users: {user_permission.can_manage_users}")
        print(f"  - can_access_products: {user_permission.can_access_products}")
        print(f"  - can_access_sales: {user_permission.can_access_sales}")
        print(f"  - can_access_purchases: {user_permission.can_access_purchases}")
        print(f"  - can_access_customers: {user_permission.can_access_customers}")
        print(f"  - can_access_suppliers: {user_permission.can_access_suppliers}")
        print(f"  - can_access_expenses: {user_permission.can_access_expenses}")
        print(f"  - can_access_reports: {user_permission.can_access_reports}")
        print(f"  - can_access_settings: {user_permission.can_access_settings}")
    except UserPermission.DoesNotExist:
        print("No UserPermission record found for this user")
        
except User.DoesNotExist:
    print("User 'royke' not found in the database")
except Exception as e:
    print(f"Error checking user: {str(e)}")