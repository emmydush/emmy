#!/usr/bin/env python
"""
Test script to verify Kinyarwanda language switching functionality
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_management.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse


def test_kinyarwanda_language_switch():
    """Test that Kinyarwanda language switching works correctly"""
    User = get_user_model()
    
    # Get the first user (assuming there's at least one)
    try:
        user = User.objects.first()
        if not user:
            print("❌ No users found in the database")
            return False
            
        print(f"User: {user.username}")
        print(f"Current language: {user.language}")
        
        # Create a test client
        client = Client()
        
        # Log in the user
        login_success = client.login(username=user.username, password="testpass123")
        if not login_success:
            print("❌ Failed to log in user with testpass123")
            # Try with the actual password from the database (might be different)
            print("Trying to create a test user instead...")
            try:
                # Create a test user
                test_user = User.objects.create_user(
                    username="testuser_kinya",
                    email="test_kinya@example.com",
                    password="testpass123",
                    language="en",
                )
                login_success = client.login(username="testuser_kinya", password="testpass123")
                if not login_success:
                    print("❌ Failed to log in test user")
                    return False
                user = test_user
            except Exception as e:
                print(f"❌ Error creating test user: {e}")
                return False
        
        print("✅ Successfully logged in")
        
        # Test switching to Kinyarwanda
        print("Testing switch to Kinyarwanda...")
        response = client.post(
            reverse("authentication:set_user_language"), 
            {"language": "rw", "next": "/"}
        )
        
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ Redirect received - language switch request successful")
            
            # Check if user language was updated
            user.refresh_from_db()
            print(f"User language after switch: {user.language}")
            
            if user.language == "rw":
                print("✅ User language successfully updated to Kinyarwanda")
                return True
            else:
                print("❌ User language was not updated")
                return False
        else:
            print("❌ Language switch request failed")
            print(f"Response content: {response.content.decode()[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error during language switch test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_kinyarwanda_language_switch()
    if success:
        print("\n🎉 Kinyarwanda language switching is working correctly!")
    else:
        print("\n💥 Kinyarwanda language switching is still not working.")