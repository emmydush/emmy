from django.db import models
from django.contrib.auth import get_user_model
import uuid
from django.utils import timezone

User = get_user_model()


class Business(models.Model):
    BUSINESS_TYPE_CHOICES = (
        ("retail", "Retail"),
        ("wholesale", "Wholesale"),
        ("manufacturing", "Manufacturing"),
        ("service", "Service"),
        ("other", "Other"),
    )

    PLAN_CHOICES = (
        ("free", "Free"),
        ("premium", "Premium"),
        ("enterprise", "Enterprise"),
    )

    STATUS_CHOICES = (
        ("active", "Active"),
        ("suspended", "Suspended"),
        ("pending", "Pending Approval"),
    )

    company_name = models.CharField(max_length=200)
    # Make owner optional to support test setups and legacy data that may
    # create businesses without assigning an owner. Production flows should
    # still set an owner when creating real businesses.
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_businesses",
        null=True,
        blank=True,
    )
    email = models.EmailField()
    business_type = models.CharField(
        max_length=20, choices=BUSINESS_TYPE_CHOICES, default="retail"
    )
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, default="free")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Businesses"

    def __str__(self):
        return self.company_name

    @property
    def user_count(self):
        # For now, we'll return a placeholder value
        # In a real implementation, this would count users associated with this business
        return 1

    def get_main_branch(self):
        """Get the main branch for this business"""
        try:
            return self.branches.get(is_main=True)
        except Branch.DoesNotExist:
            # If no main branch exists, return the first active branch
            return self.branches.filter(is_active=True).first()


class Branch(models.Model):
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="branches"
    )
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    is_main = models.BooleanField(default=False)  # type: ignore
    is_active = models.BooleanField(default=True)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business.company_name} - {self.name}"


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # type: ignore
    duration_days = models.IntegerField(help_text="Duration in days", default=30)  # type: ignore
    max_products = models.IntegerField(default=100)  # type: ignore
    max_users = models.IntegerField(default=5)  # type: ignore
    max_branches = models.IntegerField(default=1)  # type: ignore
    is_active = models.BooleanField(default=True)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)  # type: ignore
    end_date = models.DateTimeField()  # type: ignore
    is_active = models.BooleanField(default=True)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business.company_name} - {self.plan.name}"


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # type: ignore
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )
    receipt = models.FileField(upload_to="payments/receipts/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.subscription.business.company_name}"


class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key


class SystemLog(models.Model):
    """Model to store system logs"""

    LOG_LEVEL_CHOICES = (
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("critical", "Critical"),
    )

    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=10, choices=LOG_LEVEL_CHOICES)
    message = models.TextField()
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="superadmin_system_logs",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        message_str = str(self.message)
        return f"{self.level.upper()}: {message_str[:50]}..."


class SecurityEvent(models.Model):
    """Model to track security events"""

    EVENT_TYPE_CHOICES = (
        ("login_attempt", "Login Attempt"),
        ("suspicious_activity", "Suspicious Activity"),
        ("account_lockout", "Account Lockout"),
        ("password_reset", "Password Reset"),
    )

    timestamp = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="superadmin_security_events",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField()
    is_resolved = models.BooleanField(default=False)  # type: ignore
    created_at = models.DateTimeField(default=timezone.now)  # type: ignore

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.event_type} - {self.user.username if self.user else 'Unknown'}"


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_active = models.BooleanField(default=True)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class SupportTicket(models.Model):
    PRIORITY_CHOICES = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    )

    STATUS_CHOICES = (
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    )

    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ticket #{self.id}: {self.subject}"


class BranchRequest(models.Model):
    """Model for branch creation requests that require superadmin approval"""

    STATUS_CHOICES = [
        ("pending", "Pending Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    # Business requesting the branch
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="branch_requests"
    )

    # Branch details
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    is_main = models.BooleanField(default=False)

    # Request information
    requested_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="branch_requests",
    )
    requested_at = models.DateTimeField(auto_now_add=True)

    # Approval information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    approved_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="branch_approvals",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True, null=True)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Branch Request"
        verbose_name_plural = "Branch Requests"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"Branch Request: {self.name} for {self.business.company_name} - {self.status.title()}"

    def save(self, *args, **kwargs):
        # Automatically set approved_at when status changes to approved or rejected
        if self.status in ["approved", "rejected"] and not self.approved_at:
            from django.utils import timezone

            self.approved_at = timezone.now()

        super().save(*args, **kwargs)

        # If approved, automatically create the branch
        if self.status == "approved":
            self.create_branch()

    def create_branch(self):
        """Create the actual branch when the request is approved"""
        from .models import Branch

        # Create the branch with the requested details
        branch = Branch.objects.create(
            business=self.business,
            name=self.name,
            address=self.address,
            phone=self.phone,
            email=self.email,
            is_main=self.is_main,
            is_active=True,
        )

        return branch


class APIClient(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    api_key = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business.company_name} - {self.name}"


class APIRequestLog(models.Model):
    api_client = models.ForeignKey(APIClient, on_delete=models.CASCADE)
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    response_time = models.FloatField(help_text="Response time in milliseconds")
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.api_client.business.company_name} - {self.endpoint}"
