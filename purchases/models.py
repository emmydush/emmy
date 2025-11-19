from django.db import models
from products.models import Product
from suppliers.models import Supplier
from superadmin.models import Business
from superadmin.managers import BusinessSpecificManager


class PurchaseOrder(models.Model):
    # Use business-specific manager
    objects = BusinessSpecificManager()

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("ordered", "Ordered"),
        ("received", "Received"),
        ("cancelled", "Cancelled"),
    )

    # Add business relationship for multi-tenancy
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="purchase_orders", null=True
    )
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    order_date = models.DateField()
    expected_delivery_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-order_date"]

    def __str__(self):
        return f"PO-{self.pk} - {self.supplier.name}"

    @property
    def total_amount(self):
        """Calculate total amount for this purchase order"""
        total = 0
        for item in self.items.all():
            total += item.total_amount
        return total


class PurchaseItem(models.Model):
    # Use business-specific manager
    objects = BusinessSpecificManager()

    purchase_order = models.ForeignKey(
        PurchaseOrder, related_name="items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    received_quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )  # Add this field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["product__name"]

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

    @property
    def total_amount(self):
        """Calculate total amount for this item"""
        return self.quantity * self.unit_price

    @property
    def is_fully_received(self):  # Add this property
        """Check if this item is fully received"""
        return self.received_quantity >= self.quantity
