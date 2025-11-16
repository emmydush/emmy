import os
import sys
import django
import requests
import json

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_management.settings')
django.setup()

# Test the API endpoints
def test_api():
    base_url = 'http://127.0.0.1:8000'
    
    # Get token for the user
    print("Getting authentication token...")
    try:
        from authentication.models import User
        from rest_framework.authtoken.models import Token
        user = User.objects.first()
        token, created = Token.objects.get_or_create(user=user)
        auth_token = token.key
        print(f"✓ Token: {auth_token}")
    except Exception as e:
        print(f"✗ Error getting token: {e}")
        return
    
    # Set up headers with token
    headers = {
        'Authorization': f'Token {auth_token}'
    }
    
    # Test dashboard stats endpoint (this one should work without authentication according to the code)
    print("\nTesting dashboard stats endpoint...")
    try:
        response = requests.get(f'{base_url}/api/v1/dashboard/stats/')
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Dashboard stats: {data}")
        else:
            print(f"✗ Dashboard stats failed with status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ Dashboard stats error: {e}")
    
    # Test products endpoint
    print("\nTesting products endpoint...")
    try:
        response = requests.get(f'{base_url}/api/v1/products/', headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Products endpoint working. Found {data.get('count', 0)} products")
        else:
            print(f"✗ Products endpoint failed with status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ Products endpoint error: {e}")
    
    # Test sales endpoint
    print("\nTesting sales endpoint...")
    try:
        response = requests.get(f'{base_url}/api/v1/sales/', headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Sales endpoint working. Found {data.get('count', 0)} sales")
        else:
            print(f"✗ Sales endpoint failed with status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ Sales endpoint error: {e}")

if __name__ == "__main__":
    test_api()