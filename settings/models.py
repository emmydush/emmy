from django.db import models
from django.contrib.auth import get_user_model
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

User = get_user_model()


class BusinessSettings(models.Model):
    # Add foreign key to Business model for data isolation
    business = models.OneToOneField(
        "superadmin.Business",
        on_delete=models.CASCADE,
        related_name="settings",
        null=True,
        blank=True,
    )

    business_name = models.CharField(max_length=200, default="Smart Solution")
    business_address = models.TextField(default="123 Business Street, City, Country")
    business_email = models.EmailField(default="info@smartsolution.com")
    business_phone = models.CharField(max_length=20, default="+1 (555) 123-4567")
    business_logo = models.ImageField(upload_to="business/logo/", blank=True, null=True)
    currency = models.CharField(max_length=3, default="FRW")
    currency_symbol = models.CharField(max_length=10, default="FRW")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # Expiry alert settings
    expiry_alert_days = models.IntegerField(default=7, help_text="Number of days before expiry to send alerts")  # type: ignore
    near_expiry_alert_days = models.IntegerField(default=30, help_text="Number of days before expiry to send near expiry alerts")  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Business Settings"

    def __str__(self) -> str:  # type: ignore
        if self.business:
            return f"{self.business.company_name} Settings"
        return self.business_name  # type: ignore


class BackupSettings(models.Model):
    FREQUENCY_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    BACKUP_TIME_CHOICES = [
        ("00:00", "12:00 AM"),
        ("01:00", "1:00 AM"),
        ("02:00", "2:00 AM"),
        ("03:00", "3:00 AM"),
        ("04:00", "4:00 AM"),
        ("05:00", "5:00 AM"),
        ("06:00", "6:00 AM"),
        ("07:00", "7:00 AM"),
        ("08:00", "8:00 AM"),
        ("09:00", "9:00 AM"),
        ("10:00", "10:00 AM"),
        ("11:00", "11:00 AM"),
        ("12:00", "12:00 PM"),
        ("13:00", "1:00 PM"),
        ("14:00", "2:00 PM"),
        ("15:00", "3:00 PM"),
        ("16:00", "4:00 PM"),
        ("17:00", "5:00 PM"),
        ("18:00", "6:00 PM"),
        ("19:00", "7:00 PM"),
        ("20:00", "8:00 PM"),
        ("21:00", "9:00 PM"),
        ("22:00", "10:00 PM"),
        ("23:00", "11:00 PM"),
    ]

    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default="daily")  # type: ignore
    backup_time = models.CharField(max_length=5, choices=BACKUP_TIME_CHOICES, default="02:00")  # type: ignore
    retention_days = models.IntegerField(default=30, help_text="Number of days to keep backups")  # type: ignore
    is_active = models.BooleanField(default=True)  # type: ignore
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Backup Settings"

    def __str__(self) -> str:  # type: ignore
        return f"Backup Settings - {self.frequency} at {self.backup_time}"  # type: ignore


class BarcodeSettings(models.Model):
    BARCODE_TYPES = (
        ("CODE128", "Code 128"),
        ("CODE39", "Code 39"),
        ("EAN13", "EAN-13"),
        ("UPC-A", "UPC-A"),
    )

    barcode_type = models.CharField(max_length=10, choices=BARCODE_TYPES, default="CODE128")  # type: ignore
    barcode_width = models.IntegerField(default=200)  # type: ignore
    barcode_height = models.IntegerField(default=100)  # type: ignore
    display_text = models.BooleanField(default=True)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Barcode Settings"

    def __str__(self) -> str:  # type: ignore
        return f"{self.barcode_type} Settings"  # type: ignore


class EmailSettings(models.Model):
    EMAIL_BACKEND_CHOICES = (
        ("django.core.mail.backends.smtp.EmailBackend", "SMTP (Gmail, SendGrid, etc.)"),
        (
            "django.core.mail.backends.console.EmailBackend",
            "Console (Development - Print to Terminal)",
        ),
        ("django_ses.SESBackend", "Amazon SES"),
    )

    email_backend = models.CharField(max_length=100, choices=EMAIL_BACKEND_CHOICES, default="django.core.mail.backends.smtp.EmailBackend")  # type: ignore
    email_host = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="SMTP server address (e.g., smtp.gmail.com)",
    )
    email_port = models.IntegerField(default=587, help_text="SMTP port (587 for TLS, 465 for SSL)")  # type: ignore
    email_host_user = models.CharField(
        max_length=100, blank=True, null=True, help_text="Email address or username"
    )
    email_host_password = models.CharField(
        max_length=100, blank=True, null=True, help_text="Password or app password"
    )
    email_use_tls = models.BooleanField(default=True, help_text="Use TLS encryption")  # type: ignore
    email_use_ssl = models.BooleanField(default=False, help_text="Use SSL encryption")  # type: ignore
    default_from_email = models.CharField(max_length=100, default="Inventory Management System <webmaster@localhost>", help_text="Default sender email address")  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Email Settings"

    def __str__(self) -> str:  # type: ignore
        return "Email Configuration"  # type: ignore


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("VIEW", "View"),
        ("OTHER", "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    business = models.ForeignKey(
        "superadmin.Business", on_delete=models.SET_NULL, null=True, blank=True
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, null=True, blank=True)
    object_repr = models.CharField(max_length=200)
    change_message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)  # Make this field nullable
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-timestamp"]

    def __str__(self):
        business_name = self.business.company_name if self.business else "No Business"
        return f"{self.action} {self.model_name} by {self.user or 'Anonymous'} at {self.timestamp} for {business_name}"
