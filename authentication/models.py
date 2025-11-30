from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("manager", "Manager"),
        ("cashier", "Cashier"),
        ("stock_manager", "Stock Manager"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="cashier")
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    businesses = models.ManyToManyField(
        "superadmin.Business", related_name="users", blank=True
    )
    # Preferred language for the user (matches settings.LANGUAGES codes)
    language = models.CharField(
        max_length=10,
        choices=getattr(settings, "LANGUAGES", [("en", "English")]),
        default="en",
        verbose_name=_("Preferred language"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username


class UserPermission(models.Model):
    """Model to store specific permissions for users beyond role-based permissions"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="custom_permissions"
    )

    # Module permissions
    can_access_products = models.BooleanField(default=True)
    can_access_sales = models.BooleanField(default=True)
    can_access_purchases = models.BooleanField(default=True)
    can_access_customers = models.BooleanField(default=True)
    can_access_suppliers = models.BooleanField(default=True)
    can_access_expenses = models.BooleanField(default=True)
    can_access_reports = models.BooleanField(default=True)
    can_access_settings = models.BooleanField(default=False)

    # User management permissions
    can_manage_users = models.BooleanField(default=False)
    can_create_users = models.BooleanField(default=False)
    can_edit_users = models.BooleanField(default=False)
    can_delete_users = models.BooleanField(default=False)

    # Action permissions
    can_create = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    # Add branch-specific permissions
    # Branch access permissions - if empty, user can access all branches
    branches = models.ManyToManyField(
        "superadmin.Branch", related_name="user_permissions", blank=True
    )
    # If True, user can only access branches explicitly assigned to them
    restrict_to_assigned_branches = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user",)

    def __str__(self):
        return f"Permissions for {self.user.username}"


class UserThemePreference(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="theme_preference"
    )

    # Theme settings
    primary_color = models.CharField(max_length=7, default="#3498db")  # Default blue
    secondary_color = models.CharField(
        max_length=7, default="#2c3e50"
    )  # Default dark blue
    accent_color = models.CharField(max_length=7, default="#e74c3c")  # Default red
    background_color = models.CharField(
        max_length=7, default="#f8f9fa"
    )  # Default light gray
    text_color = models.CharField(max_length=7, default="#343a40")  # Default dark gray
    sidebar_color = models.CharField(
        max_length=7, default="#2c3e50"
    )  # Default dark blue
    card_color = models.CharField(max_length=7, default="#ffffff")  # Default white

    # Theme mode
    THEME_MODE_CHOICES = (
        ("light", "Light"),
        ("dark", "Dark"),
        ("custom", "Custom"),
    )
    theme_mode = models.CharField(
        max_length=10, choices=THEME_MODE_CHOICES, default="light"
    )

    # CSS variables for advanced customization
    custom_css = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "User Theme Preferences"

    def __str__(self):
        return f"{self.user.username} - Theme Preferences"
