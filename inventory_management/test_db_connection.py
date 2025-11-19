#!/usr/bin/env python
"""
Test script to verify database connection
"""
import os
import sys
import django
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_management.settings")

# Setup Django
try:
    django.setup()
except Exception as e:
    print(f"Failed to setup Django: {e}")
    sys.exit(1)


def test_database_connection():
    """Test connection to the database"""
    try:
        db_settings = settings.DATABASES["default"]
        print(f"📊 Database Engine: {db_settings['ENGINE']}")
        print(f"🗃️  Database Name: {db_settings['NAME']}")
        print(f"👤 Database User: {db_settings['USER']}")
        print(f"📍 Database Host: {db_settings['HOST']}")
        print(f"🔌 Database Port: {db_settings['PORT']}")

        # Test the actual connection
        db_conn = connections["default"]
        c = db_conn.cursor()
        print("✅ Successfully connected to the database!")
    except OperationalError as e:
        print("❌ Failed to connect to the database!")
        print(f"Error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify database credentials in local_settings.py")
        print("3. Ensure the database 'inventory_management' exists")
        print("4. Confirm the user 'inventory_user' has proper permissions")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    test_database_connection()
