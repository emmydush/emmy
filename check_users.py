import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_management.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Get all users
users = User.objects.all()
print('Total users:', users.count())
for user in users:
    print(f'  - {user.username} (role: {getattr(user, "role", "no role")}, staff: {user.is_staff})')