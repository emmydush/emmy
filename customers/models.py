from django.db import models
from typing import TYPE_CHECKING
from superadmin.models import Business
from superadmin.managers import BusinessSpecificManager

if TYPE_CHECKING:
    from django.db.models.manager import Manager


class Customer(models.Model):
    if TYPE_CHECKING:
        objects: "Manager"

    # Use business-specific manager
    objects = BusinessSpecificManager()

    # Add business relationship for multi-tenancy
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="customers", null=True
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    loyalty_points = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["first_name", "last_name"]
        # Ensure customer email is unique per business
        unique_together = ("business", "email")

    def __str__(self) -> str:  # type: ignore
        return f"{self.first_name} {self.last_name}"  # type: ignore

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
