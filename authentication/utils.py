from django.contrib import messages
from django.shortcuts import redirect
from .models import UserPermission

def check_user_permission(user, permission_type):
    """
    Check if a user has a specific permission.
    
    Args:
        user: The user object
        permission_type: The permission to check (e.g., 'can_edit', 'can_delete', 'can_create')
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    # Account owners have access to everything
    if user.role.lower() == 'admin':
        return True
    
    try:
        # Get user permissions
        user_permission = UserPermission.objects.get(user=user)
        
        # Check if user has the specific permission
        if permission_type == 'can_create':
            return user_permission.can_create
        elif permission_type == 'can_edit':
            return user_permission.can_edit
        elif permission_type == 'can_delete':
            return user_permission.can_delete
        elif permission_type == 'can_access_products':
            return user_permission.can_access_products
        elif permission_type == 'can_access_sales':
            return user_permission.can_access_sales
        elif permission_type == 'can_access_purchases':
            return user_permission.can_access_purchases
        elif permission_type == 'can_access_customers':
            return user_permission.can_access_customers
        elif permission_type == 'can_access_suppliers':
            return user_permission.can_access_suppliers
        elif permission_type == 'can_access_expenses':
            return user_permission.can_access_expenses
        elif permission_type == 'can_access_reports':
            return user_permission.can_access_reports
        elif permission_type == 'can_access_settings':
            return user_permission.can_access_settings
        elif permission_type == 'can_manage_users':
            return user_permission.can_manage_users
        elif permission_type == 'can_create_users':
            return user_permission.can_create_users
        elif permission_type == 'can_edit_users':
            return user_permission.can_edit_users
        elif permission_type == 'can_delete_users':
            return user_permission.can_delete_users
        else:
            # Default to False for unknown permissions
            return False
    except UserPermission.DoesNotExist:
        # If no custom permissions exist, default to False for edit/delete actions
        # but True for view actions
        if permission_type in ['can_create', 'can_edit', 'can_delete', 
                              'can_manage_users', 'can_create_users', 
                              'can_edit_users', 'can_delete_users']:
            return False
        else:
            return True

def require_permission(permission_type, redirect_url='dashboard:index'):
    """
    Decorator to require specific permissions for views.
    
    Args:
        permission_type: The permission required (e.g., 'can_edit', 'can_delete')
        redirect_url: URL to redirect to if permission is denied
    
    Returns:
        function: Decorator function
    """
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            # Account owners have access to everything
            if request.user.role.lower() == 'admin':
                return view_func(request, *args, **kwargs)
                
            # Check if user has the required permission
            if check_user_permission(request.user, permission_type):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You do not have permission to perform this action.')
                return redirect(redirect_url)
        return wrapped_view
    return decorator