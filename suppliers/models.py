from django.db import models
from typing import TYPE_CHECKING
from superadmin.models import Business
from superadmin.managers import BusinessSpecificManager

if TYPE_CHECKING:
    from django.db.models.manager import Manager


class Supplier(models.Model):
    if TYPE_CHECKING:
        objects: "Manager"

    # Use business-specific manager
    objects = BusinessSpecificManager()

    # Add business relationship for multi-tenancy
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="suppliers", null=True
    )
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    company = models.CharField(max_length=200, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    contact_person_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_person_email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        # Ensure supplier name is unique per business
        unique_together = ("business", "name")

    def __str__(self) -> str:  # type: ignore
        return str(self.name)  # type: ignore
