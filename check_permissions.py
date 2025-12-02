from authentication.models import User, UserPermission

# Get the user
user = User.objects.get(username='emmanuel')
print(f"User: {user.username}, Role: {user.role}")

# Check if UserPermission exists
if UserPermission.objects.filter(user=user).exists():
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
else:
    print("No UserPermission record found for this user")