import os
import shutil
import sys

# List of apps with migrations
apps_with_migrations = [
    'authentication',
    'customers',
    'expenses',
    'notifications',
    'products',
    'purchases',
    'reports',
    'sales',
    'sessions',
    'settings',
    'superadmin',
    'suppliers'
]

# Remove migration files (but keep __init__.py)
for app in apps_with_migrations:
    migrations_dir = os.path.join(app, 'migrations')
    if os.path.exists(migrations_dir):
        for file in os.listdir(migrations_dir):
            if file != '__init__.py' and file.endswith('.py'):
                file_path = os.path.join(migrations_dir, file)
                os.remove(file_path)
                print(f"Removed {file_path}")

print("Migration files cleared. Now you can run:")
print("python manage.py makemigrations")
print("python manage.py migrate")