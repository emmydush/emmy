from django.core.management.base import BaseCommand
from products.models import Category, Unit, Product
from superadmin.models import Business
from superadmin.middleware import set_current_business
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Add 10 sample products for the business'

    def handle(self, *args, **options):
        # Get the first business (assuming we have one)
        try:
            business = Business.objects.first()
            if not business:
                self.stdout.write(self.style.ERROR('No business found. Please create a business first.'))
                return
        except Business.DoesNotExist:
            self.stdout.write(self.style.ERROR('No business found. Please create a business first.'))
            return

        # Set the current business context
        set_current_business(business)

        # Get or create categories for this business
        categories_data = [
            {'name': 'Electronics', 'description': 'Electronic devices and gadgets'},
            {'name': 'Clothing', 'description': 'Apparel and fashion items'},
            {'name': 'Food & Beverages', 'description': 'Food products and beverages'},
            {'name': 'Home & Garden', 'description': 'Home improvement and garden supplies'},
        ]
        
        categories = []
        for cat_data in categories_data:
            # Get or create category for this business
            category, created = Category.objects.get_or_create(
                business=business,
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Using existing category: {category.name}')

        # Get or create units for this business
        units_data = [
            {'name': 'Piece', 'symbol': 'pc'},
            {'name': 'Kilogram', 'symbol': 'kg'},
            {'name': 'Liter', 'symbol': 'L'},
            {'name': 'Box', 'symbol': 'box'},
        ]
        
        units = []
        for unit_data in units_data:
            # Get or create unit for this business
            unit, created = Unit.objects.get_or_create(
                business=business,
                name=unit_data['name'],
                defaults={'symbol': unit_data['symbol']}
            )
            units.append(unit)
            if created:
                self.stdout.write(f'Created unit: {unit.name} ({unit.symbol})')
            else:
                self.stdout.write(f'Using existing unit: {unit.name} ({unit.symbol})')

        # Sample product data
        sample_products = [
            {
                'name': 'Smartphone X',
                'sku': 'SPX001',
                'description': 'Latest model smartphone with advanced features',
                'cost_price': Decimal('300.00'),
                'selling_price': Decimal('599.99'),
                'quantity': Decimal('50'),
                'reorder_level': Decimal('10'),
            },
            {
                'name': 'Laptop Pro',
                'sku': 'LPP001',
                'description': 'High-performance laptop for work and gaming',
                'cost_price': Decimal('800.00'),
                'selling_price': Decimal('1299.99'),
                'quantity': Decimal('25'),
                'reorder_level': Decimal('5'),
            },
            {
                'name': 'Premium T-Shirt',
                'sku': 'PTS001',
                'description': 'Comfortable cotton t-shirt in various colors',
                'cost_price': Decimal('5.00'),
                'selling_price': Decimal('19.99'),
                'quantity': Decimal('100'),
                'reorder_level': Decimal('20'),
            },
            {
                'name': 'Organic Coffee Beans',
                'sku': 'OCB001',
                'description': 'Premium roasted organic coffee beans',
                'cost_price': Decimal('8.00'),
                'selling_price': Decimal('15.99'),
                'quantity': Decimal('200'),
                'reorder_level': Decimal('30'),
            },
            {
                'name': 'Professional Garden Tools Set',
                'sku': 'PGT001',
                'description': 'Complete set of essential garden tools',
                'cost_price': Decimal('25.00'),
                'selling_price': Decimal('49.99'),
                'quantity': Decimal('40'),
                'reorder_level': Decimal('8'),
            },
            {
                'name': 'Bluetooth Speaker',
                'sku': 'BS002',
                'description': 'Portable wireless speaker with excellent sound quality',
                'cost_price': Decimal('40.00'),
                'selling_price': Decimal('79.99'),
                'quantity': Decimal('60'),
                'reorder_level': Decimal('12'),
            },
            {
                'name': 'Running Shoes',
                'sku': 'RS001',
                'description': 'Comfortable athletic shoes for running and exercise',
                'cost_price': Decimal('60.00'),
                'selling_price': Decimal('119.99'),
                'quantity': Decimal('75'),
                'reorder_level': Decimal('15'),
            },
            {
                'name': 'LED Desk Lamp',
                'sku': 'LDL001',
                'description': 'Adjustable LED desk lamp with multiple brightness settings',
                'cost_price': Decimal('15.00'),
                'selling_price': Decimal('34.99'),
                'quantity': Decimal('80'),
                'reorder_level': Decimal('10'),
            },
            {
                'name': 'Insulated Water Bottle',
                'sku': 'IWB001',
                'description': 'Insulated stainless steel water bottle',
                'cost_price': Decimal('12.00'),
                'selling_price': Decimal('24.99'),
                'quantity': Decimal('150'),
                'reorder_level': Decimal('25'),
            },
            {
                'name': 'Durable Backpack',
                'sku': 'DBP001',
                'description': 'Durable backpack with multiple compartments',
                'cost_price': Decimal('20.00'),
                'selling_price': Decimal('39.99'),
                'quantity': Decimal('90'),
                'reorder_level': Decimal('15'),
            },
        ]

        # Create products for this business
        products_created = 0
        for i, product_data in enumerate(sample_products):
            # Select random category and unit
            category = random.choice(categories)
            unit = random.choice(units)
            
            # Get or create product for this business
            product, created = Product.objects.get_or_create(
                business=business,
                sku=product_data['sku'],
                defaults={
                    'name': product_data['name'],
                    'category': category,
                    'unit': unit,
                    'description': product_data['description'],
                    'cost_price': product_data['cost_price'],
                    'selling_price': product_data['selling_price'],
                    'quantity': product_data['quantity'],
                    'reorder_level': product_data['reorder_level'],
                }
            )
            
            if created:
                self.stdout.write(f'Created product: {product.name} (SKU: {product.sku})')
                products_created += 1
            else:
                self.stdout.write(f'Product already exists: {product.name} (SKU: {product.sku})')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created/updated {products_created} sample products for business "{business.company_name}"'
            )
        )