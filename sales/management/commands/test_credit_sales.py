from django.core.management.base import BaseCommand
from django.utils import timezone
from sales.models import CreditSale, CreditPayment
from customers.models import Customer
from sales.models import Sale
from decimal import Decimal
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Test credit sales functionality'

    def handle(self, *args, **options):
        # Create a test customer if none exists
        customer, created = Customer.objects.get_or_create(
            first_name="Test",
            last_name="Customer",
            email="test@example.com",
            phone="+1234567890",
            defaults={
                "credit_limit": Decimal("1000.00"),
                "loyalty_points": Decimal("0.00")
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created test customer: {customer.full_name}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Using existing customer: {customer.full_name}')
            )
        
        # Create a test sale if none exists
        sale, created = Sale.objects.get_or_create(
            subtotal=Decimal("100.00"),
            tax=Decimal("0.00"),
            discount=Decimal("0.00"),
            total_amount=Decimal("100.00"),
            payment_method="cash",
            customer=customer,
            defaults={
                "notes": "Test sale for credit sales functionality"
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created test sale: #{sale.id}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Using existing sale: #{sale.id}')
            )
        
        # Create a credit sale
        due_date = date.today() + timedelta(days=30)
        credit_sale = CreditSale.objects.create(
            customer=customer,
            sale=sale,
            total_amount=Decimal("100.00"),
            due_date=due_date,
            notes="Test credit sale"
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created credit sale: #{credit_sale.id}')
        )
        
        # Verify initial state
        self.stdout.write(
            f'Credit sale balance: {credit_sale.balance}'
        )
        self.stdout.write(
            f'Credit sale is fully paid: {credit_sale.is_fully_paid}'
        )
        
        # Create a payment
        payment = CreditPayment.objects.create(
            credit_sale=credit_sale,
            amount=Decimal("50.00"),
            payment_method="cash",
            notes="Partial payment"
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created payment: #{payment.id}')
        )
        
        # Refresh credit sale from database
        credit_sale.refresh_from_db()
        
        # Verify updated state
        self.stdout.write(
            f'Credit sale balance after payment: {credit_sale.balance}'
        )
        self.stdout.write(
            f'Credit sale amount paid: {credit_sale.amount_paid}'
        )
        self.stdout.write(
            f'Credit sale is fully paid: {credit_sale.is_fully_paid}'
        )
        
        # Create another payment to fully pay
        payment2 = CreditPayment.objects.create(
            credit_sale=credit_sale,
            amount=Decimal("50.00"),
            payment_method="cash",
            notes="Final payment"
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created final payment: #{payment2.id}')
        )
        
        # Refresh credit sale from database
        credit_sale.refresh_from_db()
        
        # Verify final state
        self.stdout.write(
            f'Credit sale final balance: {credit_sale.balance}'
        )
        self.stdout.write(
            f'Credit sale final amount paid: {credit_sale.amount_paid}'
        )
        self.stdout.write(
            f'Credit sale is fully paid: {credit_sale.is_fully_paid}'
        )
        
        self.stdout.write(
            self.style.SUCCESS('Credit sales test completed successfully!')
        )