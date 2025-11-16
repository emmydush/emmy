from django.core.management.base import BaseCommand
from sales.models import Sale
from superadmin.models import Business
from superadmin.middleware import set_current_business
from decimal import Decimal

class Command(BaseCommand):
    help = 'Test profit calculation for sales'

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

        # Get today's sales
        from django.utils import timezone
        today = timezone.now().date()
        today_sales = Sale.objects.business_specific().filter(sale_date__date=today)
        
        self.stdout.write(f'Business: {business.company_name}')
        self.stdout.write(f'Today\'s sales count: {today_sales.count()}')
        
        total_profit = Decimal('0.00')
        for sale in today_sales:
            profit = sale.total_profit
            self.stdout.write(f'Sale #{sale.id} - Total: ${sale.total_amount}, Profit: ${profit:.2f}')
            total_profit += profit
            
        self.stdout.write(self.style.SUCCESS(f'Today\'s total profit: ${total_profit:.2f}'))