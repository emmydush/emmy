from django.core.management.base import BaseCommand
from sales.models import Sale, SaleItem
from products.models import Product
from customers.models import Customer
from superadmin.models import Business
from superadmin.middleware import set_current_business
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create a test sale with items for profit calculation testing'

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

        # Get or create a test customer
        customer, created = Customer.objects.get_or_create(
            business=business,
            email='test@example.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'Customer',
                'phone': '+1234567890',
                'address': '123 Test Street'
            }
        )
        if created:
            self.stdout.write(f'Created customer: {customer.full_name}')
        else:
            self.stdout.write(f'Using existing customer: {customer.full_name}')

        # Get a product to use in the sale
        product = Product.objects.business_specific().first()
        if not product:
            self.stdout.write(self.style.ERROR('No products found.'))
            return
            
        self.stdout.write(f'Using product: {product.name}')
        self.stdout.write(f'Product cost price: ${product.cost_price}')
        self.stdout.write(f'Product selling price: ${product.selling_price}')

        # Create a sale
        sale = Sale.objects.create(
            business=business,
            customer=customer,
            subtotal=Decimal('20000.00'),
            total_amount=Decimal('20000.00'),
            payment_method='cash'
        )
        self.stdout.write(f'Created sale: #{sale.id}')

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

        # Update sale totals
        sale.subtotal = total_price
        sale.total_amount = total_price
        sale.save()
        
        # Calculate expected profit
        expected_profit = (float(unit_price) - float(product.cost_price)) * float(quantity)
        actual_profit = sale.total_profit
        
        self.stdout.write(self.style.SUCCESS(f'Sale total: ${sale.total_amount}'))
        self.stdout.write(self.style.SUCCESS(f'Expected profit: ${expected_profit:.2f}'))
        self.stdout.write(self.style.SUCCESS(f'Actual profit from property: ${actual_profit:.2f}'))