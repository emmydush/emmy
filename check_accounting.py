import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_management.settings')
django.setup()

from django.db import connection

# Check what accounting tables exist
cursor = connection.cursor()
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'accounting_%'")
tables = cursor.fetchall()
print("Accounting tables:", [table[0] for table in tables])

# Check foreign key constraints on superadmin_business
cursor.execute("""
    SELECT 
        tc.table_name, 
        kcu.column_name, 
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name 
    FROM 
        information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name='superadmin_business'
""")
foreign_keys = cursor.fetchall()
print("Foreign keys referencing superadmin_business:", foreign_keys)