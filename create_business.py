import os
import django

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_management.settings")
django.setup()

from django.contrib.auth import get_user_model
from superadmin.models import Business

User = get_user_model()

# Get the admin user
admin = User.objects.get(username="admin")

# Check if business already exists
if not Business.objects.filter(owner=admin).exists():
    # Create a business for the admin user
    business = Business.objects.create(
        owner=admin,
        company_name="Admin Business",
        email="admin@business.com",
        plan_type="premium",
        status="active",
    )
    print(f"Created business: {business.company_name}")
else:
    print("Business already exists for admin user")
