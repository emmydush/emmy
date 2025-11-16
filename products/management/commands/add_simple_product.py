from django.core.management.base import BaseCommand
from products.models import Category, Unit, Product
from superadmin.models import Business
from superadmin.middleware import set_current_business
from decimal import Decimal

class Command(BaseCommand):
    help = 'Add a simple test product for the business'

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

        # Create a category for this business
        category, created = Category.objects.get_or_create(
            business=business,
            name='Test Category',
            defaults={'description': 'Test category for sample products'}
        )
        if created:
            self.stdout.write(f'Created category: {category.name}')
        else:
            self.stdout.write(f'Using existing category: {category.name}')

        # Create a unit for this business
        unit, created = Unit.objects.get_or_create(
            business=business,
            name='Piece',
            defaults={'symbol': 'pc'}
        )
        if created:
            self.stdout.write(f'Created unit: {unit.name} ({unit.symbol})')
        else:
            self.stdout.write(f'Using existing unit: {unit.name} ({unit.symbol})')

        # Create a product for this business
        product, created = Product.objects.get_or_create(
            business=business,
            sku='TEST001',
            defaults={
                'name': 'Test Product',
                'category': category,
                'unit': unit,
                'description': 'Test product for development',
                'cost_price': Decimal('10.00'),
                'selling_price': Decimal('20.00'),
                'quantity': Decimal('100'),
                'reorder_level': Decimal('10'),
            }
        )
        
        if created:
            self.stdout.write(f'Created product: {product.name} (SKU: {product.sku})')
        else:
            self.stdout.write(f'Product already exists: {product.name} (SKU: {product.sku})')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created/updated product for business "{business.company_name}"'
            )
        )