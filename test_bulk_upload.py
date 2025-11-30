import os
import sys
import django
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from products.models import Product, Category, Unit
from products.views import bulk_upload
from django.http import HttpRequest
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages import get_messages

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_management.settings')
django.setup()

def test_bulk_upload():
    print("Testing bulk upload functionality...")
    
    # Create a test user
    user = User.objects.create_user(username='testuser', password='testpass')
    
    # Create a mock request
    request = HttpRequest()
    request.user = user
    request.method = 'POST'
    
    # Add session and message middleware
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()
    
    middleware = MessageMiddleware()
    middleware.process_request(request)
    
    # Create a test CSV file
    csv_content = '''Name,SKU,Barcode,Category,Unit,Description,Cost Price,Selling Price,Quantity,Reorder Level,Expiry Date
Test Product 1,TEST001,123456789012,Electronics,Piece,Test product for bulk upload,10.50,15.99,100,10,2025-12-31
Test Product 2,TEST002,234567890123,Books,Piece,Another test product,5.25,9.99,50,5,2026-06-30'''
    
    csv_file = SimpleUploadedFile(
        "test_products.csv",
        csv_content.encode('utf-8'),
        content_type="text/csv"
    )
    
    request.FILES['csv_file'] = csv_file
    
    # Call the bulk upload view
    response = bulk_upload(request)
    
    # Check if products were created
    products = Product.objects.filter(sku__startswith='TEST')
    print(f"Created {products.count()} products")
    
    for product in products:
        print(f"- {product.name} ({product.sku}): Qty {product.quantity}, Price {product.selling_price}")
    
    # Test updating existing products
    print("\nTesting update functionality...")
    csv_content_update = '''Name,SKU,Barcode,Category,Unit,Description,Cost Price,Selling Price,Quantity,Reorder Level,Expiry Date
Updated Test Product 1,TEST001,123456789012,Electronics,Piece,Updated test product,12.00,18.99,150,15,2025-12-31'''
    
    csv_file_update = SimpleUploadedFile(
        "test_products_update.csv",
        csv_content_update.encode('utf-8'),
        content_type="text/csv"
    )
    
    request.FILES['csv_file'] = csv_file_update
    response = bulk_upload(request)
    
    # Check if product was updated
    updated_product = Product.objects.get(sku='TEST001')
    print(f"Updated product: {updated_product.name}, Qty: {updated_product.quantity}, Price: {updated_product.selling_price}")

if __name__ == "__main__":
    test_bulk_upload()