from django.core.management.base import BaseCommand
from sales.models import Sale, SaleItem
from products.models import Product
from superadmin.models import Business
from superadmin.middleware import set_current_business
from decimal import Decimal

class Command(BaseCommand):
    help = 'Fix sale items for a specific sale'

    def add_arguments(self, parser):
        parser.add_argument('sale_id', type=int, help='ID of the sale to fix')
        
    def handle(self, *args, **options):
        sale_id = options['sale_id']
        
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

        # Get the sale
        try:
            sale = Sale.objects.business_specific().get(id=sale_id)
        except Sale.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Sale with ID {sale_id} not found.'))
            return

        self.stdout.write(f'Sale ID: {sale.id}')
        self.stdout.write(f'Total amount: {sale.total_amount}')
        self.stdout.write(f'Current profit: {sale.total_profit}')
        self.stdout.write(f'Current items: {sale.items.count()}')

        # If the sale already has items, don't modify it
        if sale.items.count() > 0:
            self.stdout.write(self.style.WARNING(f'Sale already has {sale.items.count()} items. Not modifying.'))
            return

        # Get a product to use in the sale
        product = Product.objects.business_specific().first()
        if not product:
            self.stdout.write(self.style.ERROR('No products found.'))
            return
            
        self.stdout.write(f'Using product: {product.name}')
        self.stdout.write(f'Product cost price: ${product.cost_price}')
        self.stdout.write(f'Product selling price: ${product.selling_price}')

        # Create a sale item
        quantity = Decimal('1')
        unit_price = product.selling_price
        total_price = quantity * unit_price
        
        sale_item = SaleItem.objects.create(
            business=business,
            sale=sale,
            product=product,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price
        )
        self.stdout.write(f'Created sale item: {sale_item.product.name} x {sale_item.quantity}')

        # Update sale totals (optional, as they might already be correct)
        # sale.subtotal = total_price
        # sale.total_amount = total_price
        # sale.save()
        
        # Calculate expected profit
        expected_profit = (Decimal(str(unit_price)) - Decimal(str(product.cost_price))) * Decimal(str(quantity))
        actual_profit = sale.total_profit
        
        self.stdout.write(self.style.SUCCESS(f'Sale total: ${sale.total_amount}'))
        self.stdout.write(self.style.SUCCESS(f'Expected profit: ${expected_profit:.2f}'))
        self.stdout.write(self.style.SUCCESS(f'Actual profit from property: ${actual_profit:.2f}'))