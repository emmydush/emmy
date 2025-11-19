#!/usr/bin/env python3
"""
Demonstration script for the Real-Time Stock Levels monitoring system.

This script shows how the stock alert system works by:
1. Creating sample products with different stock levels
2. Simulating stock movements
3. Checking for alerts
4. Displaying the generated alerts
"""

import os
import sys
import django
from decimal import Decimal

# Add the project directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "inventory_management"))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()

from products.models import Product, StockAlert, StockMovement
from products.stock_monitoring import check_low_stock_alerts, check_abnormal_reduction
from superadmin.models import Business
from authentication.models import User


def demonstrate_stock_alerts():
    print("=== Real-Time Stock Levels Monitoring System ===\n")

    # Create a business
    business, created = Business.objects.get_or_create(
        name="Demo Business", email="demo@example.com"
    )
    print(f"Business: {business.name}")

    # Create a user
    user, created = User.objects.get_or_create(
        username="demouser", email="demouser@example.com"
    )
    if created:
        user.set_password("demopass123")
        user.save()
    print(f"User: {user.username}")

    # Create sample products
    product1, created = Product.objects.get_or_create(
        business=business,
        name="Smartphone",
        sku="SP001",
        defaults={
            "quantity": Decimal("15"),
            "reorder_level": Decimal("20"),
            "cost_price": Decimal("300.00"),
            "selling_price": Decimal("450.00"),
        },
    )
    print(
        f"Product 1: {product1.name} (Stock: {product1.quantity}, Reorder Level: {product1.reorder_level})"
    )

    product2, created = Product.objects.get_or_create(
        business=business,
        name="Laptop",
        sku="LP001",
        defaults={
            "quantity": Decimal("50"),
            "reorder_level": Decimal("10"),
            "cost_price": Decimal("800.00"),
            "selling_price": Decimal("1200.00"),
        },
    )
    print(
        f"Product 2: {product2.name} (Stock: {product2.quantity}, Reorder Level: {product2.reorder_level})"
    )

    # Simulate normal sales for product2 over the past week
    print("\n--- Simulating normal sales for Laptop ---")
    for i in range(7):
        quantity = Decimal("5")  # Normal daily sales
        previous_quantity = product2.quantity
        new_quantity = previous_quantity - quantity

        StockMovement.objects.create(
            business=business,
            product=product2,
            movement_type="sale",
            quantity=quantity,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            created_by=user,
        )

        product2.quantity = new_quantity
        product2.save()
        print(f"Day {i+1}: Sold {quantity} units. New stock: {product2.quantity}")

    # Simulate an abnormal sale (much higher than average)
    print("\n--- Simulating abnormal sale for Laptop ---")
    abnormal_quantity = Decimal("30")  # Much higher than the average of 5
    previous_quantity = product2.quantity
    new_quantity = previous_quantity - abnormal_quantity

    StockMovement.objects.create(
        business=business,
        product=product2,
        movement_type="sale",
        quantity=abnormal_quantity,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        created_by=user,
    )

    product2.quantity = new_quantity
    product2.save()
    print(
        f"Abnormal sale: Sold {abnormal_quantity} units. New stock: {product2.quantity}"
    )

    # Check for alerts
    print("\n--- Checking for stock alerts ---")
    check_low_stock_alerts()
    check_abnormal_reduction()

    # Display generated alerts
    print("\n--- Generated Stock Alerts ---")
    alerts = StockAlert.objects.filter(business=business).order_by("-created_at")

    if alerts.exists():
        for alert in alerts:
            print(f"⚠️  [{alert.get_alert_type_display()}] {alert.message}")
            print(f"    Product: {alert.product.name}")
            print(f"    Severity: {alert.get_severity_display()}")
            print(f"    Created: {alert.created_at}")
            print()
    else:
        print("No alerts generated.")

    print("=== Demonstration Complete ===")


if __name__ == "__main__":
    demonstrate_stock_alerts()
