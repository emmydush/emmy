from django.core.management.base import BaseCommand
from notifications.models import Notification
from products.models import Product


class Command(BaseCommand):
    help = "Update existing notifications with business context information"

    def handle(self, *args, **options):
        # Update notifications that have a related product but no business
        notifications_updated = 0

        # Get notifications with related products but no business
        notifications = Notification.objects.filter(
            related_product__isnull=False, business__isnull=True
        )

        for notification in notifications:
            # Set the business from the related product
            if hasattr(notification.related_product, "business"):
                notification.business = notification.related_product.business
                notification.save()
                notifications_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {notifications_updated} notifications with business context"
            )
        )

        # Also update notifications without related products but with recipients who own businesses
        notifications_without_products = Notification.objects.filter(
            related_product__isnull=True, business__isnull=True
        )

        notifications_updated_2 = 0
        for notification in notifications_without_products:
            # Try to associate with the recipient's business if they own one
            if hasattr(notification.recipient, "owned_businesses"):
                user_businesses = notification.recipient.owned_businesses.all()
                if user_businesses.exists():
                    # Associate with their first business
                    notification.business = user_businesses.first()
                    notification.save()
                    notifications_updated_2 += 1

        if notifications_updated_2 > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated {notifications_updated_2} notifications with user business context"
                )
            )
