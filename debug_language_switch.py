#!/usr/bin/env python
"""
Debug script to test language switching functionality
"""
import os
import sys
import django
import uuid

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_management.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse


def debug_language_switch():
    """Debug language switching functionality"""
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
                # Generate unique username
                unique_suffix = str(uuid.uuid4())[:8]
                test_user = User.objects.create_user(
                    username=f"test_debug_{unique_suffix}",
                    email=f"test_debug_{unique_suffix}@example.com",
                    password="testpass123",
                    language="en"
                )
                print(f"Created test user: {test_user.username}")
                login_success = client.login(username=f"test_debug_{unique_suffix}", password="testpass123")
                if not login_success:
                    print("❌ Failed to log in test user")
                    return False
                user = test_user
            except Exception as e:
                print(f"❌ Error creating test user: {e}")
                return False
        else:
            print("✅ Logged in successfully")
        
        # Check current language by examining session
        session = client.session
        print(f"Current session language: {session.get('_language', 'Not set')}")
        
        # Try to switch to Kinyarwanda
        print("Attempting to switch to Kinyarwanda...")
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
            
            # Check the session language after redirect
            redirect_client = Client()
            redirect_client.cookies = response.cookies
            redirect_response = redirect_client.get("/")
            session_after = redirect_client.session
            print(f"Session language after redirect: {session_after.get('_language', 'Not set')}")
            
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
    debug_language_switch()