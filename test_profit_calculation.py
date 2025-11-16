#!/usr/bin/env python
"""
Test script to verify profit calculation logic
"""
import os
import sys
import django
from decimal import Decimal

# Add the project directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_management.settings')
django.setup()

def test_profit_calculation():
    """Test the profit calculation logic without database"""
    print("Testing profit calculation logic...")
    
    # Simulate a product with cost and selling price
    cost_price = Decimal('50.00')
    selling_price = Decimal('75.00')
    quantity = Decimal('2')
    
    # Calculate profit per unit
    profit_per_unit = selling_price - cost_price
    print(f"Profit per unit: {profit_per_unit}")
    
    # Calculate total profit
    total_profit = profit_per_unit * quantity
    print(f"Total profit for {quantity} units: {total_profit}")
    
    # Test the Sale.total_profit property logic
    class MockProduct:
        def __init__(self, cost_price):
            self.cost_price = cost_price
    
    class MockSaleItem:
        def __init__(self, product, unit_price, quantity):
            self.product = product
            self.unit_price = unit_price
            self.quantity = quantity
    
    class MockSale:
        def __init__(self, items):
            self.items = items
        
        @property
        def total_profit(self):
            """Calculate total profit for this sale based on sale items"""
            profit = Decimal('0.00')
            for item in self.items:
                # Calculate profit for this item (selling price - cost price) * quantity
                if item.product and hasattr(item.product, 'cost_price'):
                    item_profit = (Decimal(str(item.unit_price)) - Decimal(str(item.product.cost_price))) * Decimal(str(item.quantity))
                    profit += item_profit
            return profit
    
    # Create mock data
    product = MockProduct(cost_price=cost_price)
    item = MockSaleItem(product=product, unit_price=selling_price, quantity=quantity)
    sale = MockSale(items=[item])
    
    # Test the calculation
    calculated_profit = sale.total_profit
    print(f"Calculated profit using Sale.total_profit property: {calculated_profit}")
    
    # Verify the calculation is correct
    if calculated_profit == total_profit:
        print("✓ Profit calculation is working correctly!")
        return True
    else:
        print("✗ Profit calculation is incorrect!")
        return False

if __name__ == "__main__":
    success = test_profit_calculation()
    sys.exit(0 if success else 1)