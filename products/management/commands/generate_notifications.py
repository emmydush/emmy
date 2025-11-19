from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import F
from products.models import Product
from notifications.models import Notification
from settings.models import BusinessSettings
from datetime import timedelta


class Command(BaseCommand):
    help = "Generate automatic notifications for low stock, expired products, and near expiry products"

    def handle(self, *args, **options):
        # Get business settings for alert thresholds
        try:
            business_settings = BusinessSettings.objects.get(id=1)
            expiry_alert_days = business_settings.expiry_alert_days
            near_expiry_alert_days = business_settings.near_expiry_alert_days
        except BusinessSettings.DoesNotExist:
            # Use default values if settings don't exist
            expiry_alert_days = 7
            near_expiry_alert_days = 30

        # Generate low stock notifications
        self.generate_low_stock_notifications()

        # Generate expired product notifications
        self.generate_expired_product_notifications()

        # Generate near expiry notifications with configurable thresholds
        self.generate_near_expiry_notifications(near_expiry_alert_days)

        # Generate urgent expiry notifications (closer to expiry)
        self.generate_urgent_expiry_notifications(expiry_alert_days)

        self.stdout.write(
            self.style.SUCCESS("Successfully generated automatic notifications")
        )

    def generate_low_stock_notifications(self):
        """Generate notifications for products with low stock"""
        low_stock_products = Product.objects.filter(
            is_active=True, quantity__lte=F("reorder_level")
        )

        for product in low_stock_products:
            # Check if notification already exists for this product
            existing_notification = Notification.objects.filter(
                notification_type="low_stock", related_product=product, is_read=False
            ).exists()

            if not existing_notification:
                Notification.create_for_all_users(
                    title=f"Low Stock Alert: {product.name}",
                    message=f'The product "{product.name}" is low on stock. Current quantity: {product.quantity}, Reorder level: {product.reorder_level}',
                    notification_type="low_stock",
                    related_product=product,
                )

    def generate_expired_product_notifications(self):
        """Generate notifications for expired products"""
        today = timezone.now().date()
        expired_products = Product.objects.filter(is_active=True, expiry_date__lt=today)

        for product in expired_products:
            # Check if notification already exists for this product
            existing_notification = Notification.objects.filter(
                notification_type="expired_product",
                related_product=product,
                is_read=False,
            ).exists()

            if not existing_notification:
                Notification.create_for_all_users(
                    title=f"Expired Product: {product.name}",
                    message=f'The product "{product.name}" has expired. Expiry date: {product.expiry_date}',
                    notification_type="expired_product",
                    related_product=product,
                )

    def generate_near_expiry_notifications(self, days_threshold):
        """Generate notifications for products nearing expiry (early warning)"""
        today = timezone.now().date()
        near_expiry_date = today + timedelta(days=days_threshold)
        near_expiry_products = Product.objects.filter(
            is_active=True, expiry_date__gte=today, expiry_date__lte=near_expiry_date
        )

        for product in near_expiry_products:
            # Check if notification already exists for this product
            existing_notification = Notification.objects.filter(
                notification_type="near_expiry", related_product=product, is_read=False
            ).exists()

            if not existing_notification:
                days_until_expiry = (product.expiry_date - today).days
                Notification.create_for_all_users(
                    title=f"Product Nearing Expiry: {product.name}",
                    message=f'The product "{product.name}" will expire in {days_until_expiry} days. Expiry date: {product.expiry_date}',
                    notification_type="near_expiry",
                    related_product=product,
                )

    def generate_urgent_expiry_notifications(self, days_threshold):
        """Generate urgent notifications for products very close to expiry"""
        today = timezone.now().date()
        urgent_expiry_date = today + timedelta(days=days_threshold)
        urgent_expiry_products = Product.objects.filter(
            is_active=True, expiry_date__gte=today, expiry_date__lte=urgent_expiry_date
        )

        for product in urgent_expiry_products:
            # Check if urgent notification already exists for this product
            existing_notification = Notification.objects.filter(
                notification_type="near_expiry",  # Using same type but with urgent message
                related_product=product,
                is_read=False,
                title__icontains="Urgent",  # Check if urgent notification exists
            ).exists()

            if not existing_notification:
                days_until_expiry = (product.expiry_date - today).days
                Notification.create_for_all_users(
                    title=f"Urgent: Product Expiring Soon: {product.name}",
                    message=f'URGENT: The product "{product.name}" will expire in {days_until_expiry} days. Expiry date: {product.expiry_date}. Please take immediate action.',
                    notification_type="near_expiry",
                    related_product=product,
                )
