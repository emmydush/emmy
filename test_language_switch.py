#!/usr/bin/env python
"""
Test script to verify language switching functionality
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

def test_language_switching():
    """Test that language switching works correctly"""
    User = get_user_model()
    
    # Create a test user
    user = User.objects.create_user(
        username='testuser_lang',
        email='test_lang@example.com',
        password='testpass123',
        language='en'
    )
    
    # Create a test client
    client = Client()
    
    # Log in the user
    login_success = client.login(username='testuser', password='testpass123')
    if not login_success:
        print("❌ Failed to log in test user")
        return False
    
    # Check initial language
    response = client.get('/')
    print(f"Initial language: {response.context['LANGUAGE_CODE']}")
    
    # Test switching to Kinyarwanda
    response = client.post(reverse('authentication:set_user_language'), {
        'language': 'rw',
        'next': '/'
    })
    
    if response.status_code != 302:
        print("❌ Failed to switch to Kinyarwanda - incorrect status code")
        return False
    
    # Check that the user's language was updated
    user.refresh_from_db()
    if user.language != 'rw':
        print("❌ User language was not updated to Kinyarwanda")
        return False
    
    print("✅ Language switching test passed!")
    return True

if __name__ == '__main__':
    test_language_switching()