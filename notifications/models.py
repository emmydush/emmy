from django.db import models
from django.conf import settings
from django.utils import timezone
from products.models import Product
from superadmin.models import Business


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ("low_stock", "Low Stock"),
        ("expired_product", "Expired Product"),
        ("near_expiry", "Near Expiry"),
        ("pending_order", "Pending Order"),
        ("overdue_payment", "Overdue Payment"),
        ("system", "System"),
    )

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, null=True, blank=True
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    related_product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_read = models.BooleanField(default=False)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"

    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

    @classmethod
    def create_for_all_users(
        cls, title, message, notification_type, related_product=None
    ):
        """Create a notification for all users in the same business as the product"""
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # If there's a related product, only notify users in the same business
        if related_product and hasattr(related_product, "business"):
            business = related_product.business
            # Get users who own or are associated with this business
            users = User.objects.filter(owned_businesses=business)
        else:
            # Fallback to all users if no product or business context
            users = User.objects.all()

        notifications = []
        for user in users:
            notification = cls(
                recipient=user,
                business=(
                    related_product.business
                    if related_product and hasattr(related_product, "business")
                    else None
                ),
                title=title,
                message=message,
                notification_type=notification_type,
                related_product=related_product,
            )
            notification.save()
            notifications.append(notification)

        return notifications

    @classmethod
    def create_for_user(
        cls, user, title, message, notification_type, related_product=None
    ):
        """Create a notification for a specific user"""
        return cls.objects.create(
            recipient=user,
            business=(
                related_product.business
                if related_product and hasattr(related_product, "business")
                else None
            ),
            title=title,
            message=message,
            notification_type=notification_type,
            related_product=related_product,
        )
