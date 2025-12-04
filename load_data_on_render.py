#!/usr/bin/env python
"""
Script to load data on Render after deployment
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_management.settings')
django.setup()

from django.core.management import execute_from_command_line

def load_data():
    """Load data from backup file"""
    try:
        print("Loading data from backup...")
        execute_from_command_line(['manage.py', 'loaddata', 'db_backup.json'])
        print("Data loaded successfully!")
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    load_data()