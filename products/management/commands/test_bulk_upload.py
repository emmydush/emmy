import csv
import io
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.messages import get_messages
from django.contrib.auth import get_user_model
from products.models import Product, Category, Unit
from products.views import bulk_upload
from django.http import HttpRequest
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from superadmin.models import Business
from superadmin.middleware import set_current_business

User = get_user_model()

class Command(BaseCommand):
    help = 'Test bulk upload functionality'

    def handle(self, *args, **options):
        self.stdout.write('Testing bulk upload functionality...')
        
        # Create a test user
        user, created = User.objects.get_or_create(username='testuser')
        if created:
            user.set_password('testpass')
            user.save()
        
        # Create a test business
        business, created = Business.objects.get_or_create(
            company_name='Test Business',
            defaults={
                'email': 'test@example.com',
                'business_type': 'retail',
                'plan_type': 'free',
                'status': 'active'
            }
        )
        
        # Set the current business context
        set_current_business(business)
        
        # Create a mock request
        request = HttpRequest()
        request.user = user
        request.method = 'POST'
        
        # Add session and message middleware
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        # Set the business in session
        request.session['current_business_id'] = business.id
        
        middleware = MessageMiddleware(lambda req: None)
        middleware.process_request(request)
        
        # Create a test CSV file content
        csv_content = '''Name,SKU,Barcode,Category,Unit,Description,Cost Price,Selling Price,Quantity,Reorder Level,Expiry Date
Test Product 1,TEST001,123456789012,Electronics,Piece,Test product for bulk upload,10.50,15.99,100,10,2025-12-31
Test Product 2,TEST002,234567890123,Books,Piece,Another test product,5.25,9.99,50,5,2026-06-30
Test Product 3,TEST003,,Clothing,Piece,Product without barcode,20.00,35.00,25,3,'''
        
        # Simulate file upload
        from django.core.files.uploadedfile import SimpleUploadedFile
        csv_file = SimpleUploadedFile(
            "test_products.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )
        
        request.FILES['csv_file'] = csv_file
        
        # Call the bulk upload view
        response = bulk_upload(request)
        
        # Check messages
        storage = get_messages(request)
        for message in storage:
            self.stdout.write(f'Message: {message}')
        
        # Check if products were created
        products = Product.objects.filter(sku__startswith='TEST')
        self.stdout.write(f'Created {products.count()} products')
        
        for product in products:
            self.stdout.write(f'- {product.name} ({product.sku}): Qty {product.quantity}, Price {product.selling_price}')
        
        # Test updating existing products
        self.stdout.write('\nTesting update functionality...')
        csv_content_update = '''Name,SKU,Barcode,Category,Unit,Description,Cost Price,Selling Price,Quantity,Reorder Level,Expiry Date
Updated Test Product 1,TEST001,123456789012,Electronics,Piece,Updated test product,12.00,18.99,150,15,2025-12-31'''
        
        csv_file_update = SimpleUploadedFile(
            "test_products_update.csv",
            csv_content_update.encode('utf-8'),
            content_type="text/csv"
        )
        
        request.FILES['csv_file'] = csv_file_update
        response = bulk_upload(request)
        
        # Check messages
        storage = get_messages(request)
        for message in storage:
            self.stdout.write(f'Message: {message}')
        
        # Check if product was updated
        try:
            updated_product = Product.objects.get(sku='TEST001')
            self.stdout.write(f'Updated product: {updated_product.name}, Qty: {updated_product.quantity}, Price: {updated_product.selling_price}')
        except Product.DoesNotExist:
            self.stdout.write('Product TEST001 not found after update')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully tested bulk upload functionality')
        )