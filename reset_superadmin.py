#!/usr/bin/env python
"""
Script to reset the superadmin password.
Run this script from the project root directory.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_management.settings')
django.setup()

from authentication.models import User

def reset_superadmin_password(username='admin', new_password='admin123'):
    """
    Reset the password for a superadmin user
    
    Args:
        username (str): Username of the superadmin user
        new_password (str): New password to set
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        user = User.objects.get(username=username, is_superuser=True)
        user.set_password(new_password)
        user.save()
        print(f"Successfully reset password for superadmin user '{username}'")
        return True
    except User.DoesNotExist:
        print(f"Superadmin user '{username}' does not exist")
        return False
    except Exception as e:
        print(f"Error resetting password: {e}")
        return False

if __name__ == "__main__":
    # You can modify these values as needed
    USERNAME = "admin"
    NEW_PASSWORD = "admin123"
    
    print("Resetting superadmin password...")
    success = reset_superadmin_password(USERNAME, NEW_PASSWORD)
    
    if success:
        print("Password reset completed successfully!")
        print(f"Username: {USERNAME}")
        print(f"New Password: {NEW_PASSWORD}")
        print("\nPlease change this password after logging in for security reasons.")
    else:
        print("Failed to reset password.")
        sys.exit(1)