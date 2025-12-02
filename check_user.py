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

# Check the user
try:
    user = User.objects.get(username='emmanuel')
    print(f"User: {user.username}")
    print(f"Role: {user.role}")
    
    # Check if user has a business
    if user.owned_businesses.exists():
        business = user.owned_businesses.first()
        print(f"Owned business: {business.company_name}")
        print(f"Business status: {business.status}")
    else:
        print("User does not own any businesses")
        
    # Check if user has permissions
    try:
        perm = UserPermission.objects.get(user=user)
        print("User permissions found:")
        print(f"- can_create: {perm.can_create}")
        print(f"- can_edit: {perm.can_edit}")
        print(f"- can_delete: {perm.can_delete}")
        print(f"- can_manage_users: {perm.can_manage_users}")
        print(f"- can_access_products: {perm.can_access_products}")
        print(f"- can_access_sales: {perm.can_access_sales}")
        print(f"- can_access_purchases: {perm.can_access_purchases}")
        print(f"- can_access_customers: {perm.can_access_customers}")
        print(f"- can_access_suppliers: {perm.can_access_suppliers}")
        print(f"- can_access_expenses: {perm.can_access_expenses}")
    except UserPermission.DoesNotExist:
        print("No UserPermission record found for this user")
        
except User.DoesNotExist:
    print("User 'emmanuel' not found")