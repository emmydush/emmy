from django.db import models
from django.urls import reverse
from typing import TYPE_CHECKING
import uuid
import os
from django.core.files.base import ContentFile
from io import BytesIO
import re

# Import the Business model for multi-tenancy
from superadmin.models import Business
from superadmin.managers import BusinessSpecificManager

if TYPE_CHECKING:
    from django.db.models.manager import Manager


class Category(models.Model):
    if TYPE_CHECKING:
        objects: "Manager"

    # Use business-specific manager
    objects = BusinessSpecificManager()

    # Add business relationship for multi-tenancy
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="categories", null=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]
        # Ensure category names are unique per business
        unique_together = ("business", "name")

    def __str__(self) -> str:  # type: ignore
        return str(self.name)  # type: ignore


class Unit(models.Model):
    if TYPE_CHECKING:
        objects: "Manager"

    # Use business-specific manager
    objects = BusinessSpecificManager()

    # Add business relationship for multi-tenancy
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="units", null=True
    )
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ensure unit names and symbols are unique per business
        unique_together = (("business", "name"), ("business", "symbol"))

    def __str__(self) -> str:  # type: ignore
        return f"{self.name} ({self.symbol})"  # type: ignore


class Product(models.Model):
    if TYPE_CHECKING:
        objects: "Manager"

    # Use business-specific manager
    objects = BusinessSpecificManager()

    # Add business relationship for multi-tenancy
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="products", null=True
    )

    BARCODE_FORMAT_CHOICES = [
        ("code128", "Code 128 (High Density)"),
        ("ean13", "EAN-13 (Retail Standard)"),
        ("upca", "UPC-A (Retail Standard)"),
    ]

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    barcode_format = models.CharField(
        max_length=20, choices=BARCODE_FORMAT_CHOICES, default="code128"
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expiry_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        # Ensure SKU is unique per business
        unique_together = ("business", "sku")

    def __str__(self) -> str:  # type: ignore
        return str(self.name)  # type: ignore

    def save(self, *args, **kwargs):
        # Auto-generate barcode if not provided
        is_new = self.pk is None
        if not self.barcode:
            self.barcode = self.generate_barcode()

        super().save(*args, **kwargs)

        # Generate barcode image after saving (so we have a pk)
        if is_new:
            self.generate_barcode_image()

    def generate_barcode(self):
        """Generate a unique barcode for the product based on selected format"""
        # Use SKU as base, or generate a unique identifier if SKU is not suitable
        if self.sku:
            # Create a simple numeric barcode from SKU
            # Extract digits from SKU and ensure it's unique
            sku_str = str(self.sku)  # Convert to string to ensure it's iterable
            base_code = "".join([char for char in sku_str if char.isdigit()])

            # If no digits in SKU, generate a unique code
            if not base_code:
                base_code = str(uuid.uuid4().int)[:12]
        else:
            # Generate a unique 12-digit code
            base_code = str(uuid.uuid4().int)[:12]

        # Format the barcode according to the selected format
        if self.barcode_format == "ean13":
            # EAN-13 requires 12 digits + 1 check digit = 13 total
            base_code = re.sub(r"\D", "", base_code)[:12].ljust(12, "0")
            barcode = self._generate_ean13(base_code)
        elif self.barcode_format == "upca":
            # UPC-A requires 11 digits + 1 check digit = 12 total
            base_code = re.sub(r"\D", "", base_code)[:11].ljust(11, "0")
            barcode = self._generate_upca(base_code)
        else:
            # Code128 can handle variable length and alphanumeric
            barcode = base_code[:20]  # Limit to 20 characters for Code128

        # Ensure the barcode is unique within the business
        counter = 1
        original_barcode = barcode
        while (
            Product.objects.filter(business=self.business, barcode=barcode)
            .exclude(pk=self.pk)
            .exists()
        ):
            # If we've tried too many times, generate a completely new base
            if counter > 100:
                base_code = str(uuid.uuid4().int)[:12]
                if self.barcode_format == "ean13":
                    base_code = re.sub(r"\D", "", base_code)[:12].ljust(12, "0")
                    barcode = self._generate_ean13(base_code)
                elif self.barcode_format == "upca":
                    base_code = re.sub(r"\D", "", base_code)[:11].ljust(11, "0")
                    barcode = self._generate_upca(base_code)
                else:
                    barcode = base_code[:20]
                counter = 1
                original_barcode = barcode
            else:
                # Append counter to make it unique
                if self.barcode_format == "ean13":
                    # For EAN-13, we need to regenerate with a different base
                    modified_base = base_code[:-2] + str(counter).zfill(2)
                    barcode = self._generate_ean13(
                        re.sub(r"\D", "", modified_base)[:12].ljust(12, "0")
                    )
                elif self.barcode_format == "upca":
                    # For UPC-A, we need to regenerate with a different base
                    modified_base = base_code[:-2] + str(counter).zfill(2)
                    barcode = self._generate_upca(
                        re.sub(r"\D", "", modified_base)[:11].ljust(11, "0")
                    )
                else:
                    # For Code128, we can just append the counter
                    barcode = original_barcode + str(counter)
            counter += 1

        return barcode

    def _generate_ean13(self, base_code):
        """Generate a valid EAN-13 barcode with check digit"""
        # Ensure base code is 12 digits
        base_code = base_code[:12].ljust(12, "0")

        # Calculate check digit
        # Sum odd positions (1st, 3rd, 5th, etc.)
        odd_sum = sum(int(base_code[i]) for i in range(0, 12, 2))
        # Sum even positions (2nd, 4th, 6th, etc.) and multiply by 3
        even_sum = sum(int(base_code[i]) for i in range(1, 12, 2)) * 3
        # Total sum
        total = odd_sum + even_sum
        # Check digit is the number needed to make total divisible by 10
        check_digit = (10 - (total % 10)) % 10

        return base_code + str(check_digit)

    def _generate_upca(self, base_code):
        """Generate a valid UPC-A barcode with check digit"""
        # Ensure base code is 11 digits
        base_code = base_code[:11].ljust(11, "0")

        # Calculate check digit
        # Sum odd positions (1st, 3rd, 5th, etc.) and multiply by 3
        odd_sum = sum(int(base_code[i]) for i in range(0, 11, 2)) * 3
        # Sum even positions (2nd, 4th, 6th, etc.)
        even_sum = sum(int(base_code[i]) for i in range(1, 11, 2))
        # Total sum
        total = odd_sum + even_sum
        # Check digit is the number needed to make total divisible by 10
        check_digit = (10 - (total % 10)) % 10

        return base_code + str(check_digit)

    def generate_barcode_image(self):
        """Generate and save a barcode image for the product"""
        if not self.barcode:
            return None

        try:
            from .utils import generate_product_barcode_image

            barcode_buffer = generate_product_barcode_image(self)

            if barcode_buffer:
                # Ensure the barcodes directory exists
                from django.conf import settings

                barcodes_dir = os.path.join(settings.MEDIA_ROOT, "barcodes")
                os.makedirs(barcodes_dir, exist_ok=True)

                # Save the barcode image to the media directory
                filename = f"barcode_{self.pk}.png"
                filepath = os.path.join("barcodes", filename)

                # Save the image file
                from django.core.files.storage import default_storage

                default_storage.save(filepath, ContentFile(barcode_buffer.getvalue()))

                return filepath
        except Exception as e:
            print(f"Error generating barcode image: {e}")

        return None

    def get_absolute_url(self):
        return reverse("products:detail", kwargs={"pk": self.pk})

    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level

    @property
    def profit_margin(self):
        if float(self.cost_price) > 0:  # type: ignore
            return ((float(self.selling_price) - float(self.cost_price)) / float(self.cost_price)) * 100  # type: ignore
        return 0

    @property
    def profit_per_unit(self):
        """Calculate profit per unit of this product"""
        return float(self.selling_price) - float(self.cost_price)  # type: ignore

    @property
    def total_profit(self):
        """Calculate total profit based on current quantity"""
        return self.profit_per_unit * float(self.quantity)  # type: ignore


class StockAdjustment(models.Model):
    """Model for stock adjustment requests that require approval"""

    # Use business-specific manager
    objects = BusinessSpecificManager()

    ADJUSTMENT_TYPE_CHOICES = [
        ("in", "Stock In"),
        ("out", "Stock Out"),
    ]

    REASON_CHOICES = [
        ("expired", "Expired Items"),
        ("damaged", "Damaged Items"),
        ("lost", "Lost Items"),
        ("found", "Found Items"),
        ("correction", "Inventory Correction"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    # Add business relationship for multi-tenancy
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="stock_adjustments", null=True
    )

    # Product being adjusted
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="adjustments"
    )

    # Adjustment details
    adjustment_type = models.CharField(max_length=10, choices=ADJUSTMENT_TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True, null=True)

    # Request information
    requested_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="stock_requests",
    )
    requested_at = models.DateTimeField(auto_now_add=True)

    # Approval information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    approved_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_approvals",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True, null=True)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Stock Adjustment"
        verbose_name_plural = "Stock Adjustments"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.adjustment_type.title()} {self.quantity} {self.product.name} - {self.status.title()}"

    def save(self, *args, **kwargs):
        # Automatically set approved_at when status changes to approved or rejected
        if self.status in ["approved", "rejected"] and not self.approved_at:
            from django.utils import timezone

            self.approved_at = timezone.now()

        super().save(*args, **kwargs)

        # If approved, automatically adjust the product quantity and track movement
        if self.status == "approved":
            self.process_adjustment()

    def process_adjustment(self):
        """Process the stock adjustment by updating the product quantity and tracking movement"""
        from decimal import Decimal
        from .models import StockMovement

        # Track the stock movement before updating
        previous_quantity = self.product.quantity
        adjustment_quantity = Decimal(str(self.quantity))

        if self.adjustment_type == "in":
            new_quantity = previous_quantity + adjustment_quantity
        else:  # out
            new_quantity = previous_quantity - adjustment_quantity

        # Track stock movement for analysis
        StockMovement.objects.create(
            business=self.business,
            product=self.product,
            movement_type="adjustment",
            quantity=adjustment_quantity,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            reference_id=str(self.id),
            reference_model="StockAdjustment",
            created_by=self.approved_by,
        )

        # Update product quantity
        self.product.quantity = new_quantity
        self.product.save()


class StockAlert(models.Model):
    """Model for stock-related alerts"""

    # Use business-specific manager
    objects = BusinessSpecificManager()

    ALERT_TYPE_CHOICES = [
        ("low_stock", "Low Stock"),
        ("abnormal_reduction", "Abnormal Reduction"),
        ("fast_moving", "Fast Moving"),
        ("expired", "Expired Items"),
    ]

    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    # Add business relationship for multi-tenancy
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="stock_alerts", null=True
    )

    # Product related to this alert
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="stock_alerts"
    )

    # Alert details
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(
        max_length=10, choices=SEVERITY_CHOICES, default="medium"
    )
    message = models.TextField()

    # Stock information
    current_stock = models.DecimalField(max_digits=10, decimal_places=2)
    previous_stock = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    threshold = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Resolution information
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_alerts",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Stock Alert"
        verbose_name_plural = "Stock Alerts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.product.name}"

    @property
    def alert_icon(self):
        """Return appropriate icon for alert type"""
        icons = {
            "low_stock": "exclamation-triangle",
            "abnormal_reduction": "chart-line",
            "fast_moving": "bolt",
            "expired": "calendar-times",
        }
        return icons.get(self.alert_type, "exclamation-circle")

    @property
    def severity_badge_class(self):
        """Return appropriate Bootstrap badge class for severity"""
        classes = {
            "low": "secondary",
            "medium": "warning",
            "high": "danger",
            "critical": "danger",
        }
        return classes.get(self.severity, "secondary")


class StockMovement(models.Model):
    """Model for tracking stock movements for analysis"""

    # Use business-specific manager
    objects = BusinessSpecificManager()

    MOVEMENT_TYPE_CHOICES = [
        ("sale", "Sale"),
        ("purchase", "Purchase"),
        ("adjustment", "Adjustment"),
        ("transfer", "Transfer"),
    ]

    # Add business relationship for multi-tenancy
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="stock_movements", null=True
    )

    # Product being moved
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="movements"
    )

    # Movement details
    movement_type = models.CharField(max_length=15, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    previous_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    new_quantity = models.DecimalField(max_digits=10, decimal_places=2)

    # Reference information
    reference_id = models.CharField(max_length=100, null=True, blank=True)
    reference_model = models.CharField(max_length=50, null=True, blank=True)

    # User who created the movement
    created_by = models.ForeignKey(
        "authentication.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Stock Movement"
        verbose_name_plural = "Stock Movements"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name} ({self.quantity})"
