import os
import sys
import django
from decimal import Decimal

# Add the project directory to Python path
sys.path.append('e:/AI')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_management.settings')
django.setup()

from sales.models import Sale, SaleItem
from expenses.models import Expense
from superadmin.models import Business
from superadmin.middleware import set_current_business
from django.db.models import Sum

def check_profit_calculation():
    # Get the business
    business = Business.objects.first()
    set_current_business(business)
    
    # Calculate sales revenue
    sales_revenue = Sale.objects.business_specific().aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    print(f"Sales Revenue: FRW {sales_revenue}")
    
    # Calculate COGS
    sale_items = SaleItem.objects.business_specific()
    cogs = Decimal('0')
    for item in sale_items:
        cogs += Decimal(str(item.product.cost_price)) * Decimal(str(item.quantity))
    print(f"COGS: FRW {cogs}")
    
    # Calculate expenses
    expenses_total = Expense.objects.business_specific().aggregate(total=Sum('amount'))['total'] or Decimal('0')
    print(f"Expenses: FRW {expenses_total}")
    
    # Calculate profits
    gross_profit = sales_revenue - cogs
    net_profit = gross_profit - expenses_total
    
    print(f"Gross Profit: FRW {gross_profit}")
    print(f"Net Profit: FRW {net_profit}")
    
    # Verify the numbers from the user's question
    print("\n--- Verification ---")
    print(f"Is Sales Revenue (FRW 45000.00) correct? {float(sales_revenue) == 45000.0}")
    print(f"Is COGS (FRW 15000.00) correct? {float(cogs) == 15000.0}")
    print(f"Is Gross Profit (FRW 30000.00) correct? {float(gross_profit) == 30000.0}")
    print(f"Is Net Profit (FRW 30000.00) correct? {float(net_profit) == 30000.0}")

if __name__ == "__main__":
    check_profit_calculation()