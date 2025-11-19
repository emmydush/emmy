from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from products.models import Product, StockAlert, StockMovement
from products.stock_monitoring import check_low_stock_alerts, check_abnormal_reduction
from superadmin.models import Business
from authentication.models import User


class StockAlertTestCase(TestCase):
    def setUp(self):
        # Create a business
        self.business = Business.objects.create(
            name="Test Business", email="test@example.com"
        )

        # Create a user
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="testpass123"
        )

        # Create a product
        self.product = Product.objects.create(
            business=self.business,
            name="Test Product",
            sku="TEST001",
            quantity=Decimal("100"),
            reorder_level=Decimal("20"),
            cost_price=Decimal("10.00"),
            selling_price=Decimal("15.00"),
        )

    def test_low_stock_alert_creation(self):
        """Test that low stock alerts are created correctly"""
        # Set product quantity below reorder level
        self.product.quantity = Decimal("10")
        self.product.save()

        # Check for low stock alerts
        check_low_stock_alerts()

        # Verify that an alert was created
        alerts = StockAlert.objects.filter(
            business=self.business, product=self.product, alert_type="low_stock"
        )
        self.assertEqual(alerts.count(), 1)

        # Verify alert details
        alert = alerts.first()
        self.assertEqual(alert.severity, "high")
        self.assertIn("⚠️ Low stock – possible missing items", alert.message)
        self.assertEqual(alert.current_stock, Decimal("10"))

    def test_abnormal_reduction_detection(self):
        """Test that abnormal stock reductions are detected"""
        # Create some normal sales movements
        for i in range(5):
            StockMovement.objects.create(
                business=self.business,
                product=self.product,
                movement_type="sale",
                quantity=Decimal("5"),
                previous_quantity=Decimal("100") - (i * 5),
                new_quantity=Decimal("100") - ((i + 1) * 5),
                created_by=self.user,
            )

        # Create an abnormal sale (much higher than average)
        StockMovement.objects.create(
            business=self.business,
            product=self.product,
            movement_type="sale",
            quantity=Decimal("50"),  # This is much higher than the average of 5
            previous_quantity=Decimal("75"),
            new_quantity=Decimal("25"),
            created_by=self.user,
        )

        # Check for abnormal reductions
        check_abnormal_reduction()

        # Verify that an alert was created
        alerts = StockAlert.objects.filter(
            business=self.business,
            product=self.product,
            alert_type="abnormal_reduction",
        )
        self.assertEqual(alerts.count(), 1)

        # Verify alert details
        alert = alerts.first()
        self.assertEqual(alert.severity, "high")
        self.assertIn("⚠️ Product Test Product reducing abnormally", alert.message)
