from django.db import models
from superadmin.models import Business

class OfflineSale(models.Model):
    """
    Model to store sales data when offline mode is active
    """
    SALE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
    ]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='offline_sales')
    customer_id = models.IntegerField(null=True, blank=True)
    payment_method = models.CharField(max_length=20, default='cash')
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # type: ignore
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # type: ignore
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    cart_items = models.JSONField()  # Store cart items as JSON
    status = models.CharField(max_length=10, choices=SALE_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Offline Sale'
        verbose_name_plural = 'Offline Sales'
    
    def __str__(self):
        return f"Offline Sale #{self.id} - {self.business.company_name} - {self.total_amount}"

class OfflineSettings(models.Model):
    """
    Model to store offline mode settings
    """
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name='offline_settings')
    is_offline_mode = models.BooleanField(default=False)  # type: ignore
    last_synced = models.DateTimeField(null=True, blank=True)
    sync_interval = models.IntegerField(default=300)  # type: ignore  # Sync interval in seconds (5 minutes)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Offline Settings'
        verbose_name_plural = 'Offline Settings'
    
    def __str__(self):
        return f"Offline Settings for {self.business.company_name}"