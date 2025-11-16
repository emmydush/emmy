from django.core.management.base import BaseCommand
from products.models import Product, Category, Unit
from superadmin.models import Business
from superadmin.middleware import set_current_business

class Command(BaseCommand):
    help = 'Debug product category and unit associations'

    def handle(self, *args, **options):
        # Get the first business
        try:
            business = Business.objects.first()
            if not business:
                self.stdout.write(self.style.ERROR('No business found.'))
                return
        except Business.DoesNotExist:
            self.stdout.write(self.style.ERROR('No business found.'))
            return

        # Set the current business context
        set_current_business(business)

        # Get products with business context
        products = Product.objects.business_specific().select_related('category', 'unit')[:5]
        
        self.stdout.write(f'Business: {business.company_name}')
        self.stdout.write(f'Total products: {Product.objects.business_specific().count()}')
        self.stdout.write('Sample products:')
        
        for product in products:
            category_name = product.category.name if product.category else 'None'
            unit_name = product.unit.name if product.unit else 'None'
            unit_symbol = product.unit.symbol if product.unit else 'None'
            
            self.stdout.write(f'  - {product.name} (SKU: {product.sku})')
            self.stdout.write(f'    Category: {category_name}')
            self.stdout.write(f'    Unit: {unit_name} ({unit_symbol})')
            self.stdout.write(f'    Price: ${product.selling_price}')
            self.stdout.write('')