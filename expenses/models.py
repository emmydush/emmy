from django.db import models
from superadmin.models import Business
from superadmin.managers import BusinessSpecificManager


class ExpenseCategory(models.Model):
    # Use business-specific manager
    objects = BusinessSpecificManager()

    # Add business relationship for multi-tenancy
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="expense_categories", null=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Expense Categories"
        ordering = ["name"]
        # Ensure category names are unique per business
        unique_together = ("business", "name")

    def __str__(self):
        return self.name


class Expense(models.Model):
    # Use business-specific manager
    objects = BusinessSpecificManager()

    # Add business relationship for multi-tenancy
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="expenses", null=True
    )
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    receipt = models.FileField(upload_to="expenses/receipts/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.category.name} - ${self.amount}"
