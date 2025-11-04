from django.db import models
from products.models import Product
from customers.models import Customer
from superadmin.models import Business
from superadmin.managers import BusinessSpecificManager
from authentication.models import User

class Cart(models.Model):
    objects = BusinessSpecificManager()
    # Add business relationship for multi-tenancy
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='carts', null=True)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        else:
            return f"Cart for session {self.session_key}"

    def get_total_items(self):
        return sum(item.quantity for item in self.cartitem_set.all())

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.cartitem_set.all())

class CartItem(models.Model):
    # Add business relationship for multi-tenancy
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='cart_items', null=True)
    
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)  # type: ignore
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        return self.quantity * self.unit_price

class Sale(models.Model):
    objects = BusinessSpecificManager()
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    # Add business relationship for multi-tenancy
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='sales', null=True)
    
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    sale_date = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # type: ignore
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # type: ignore
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # type: ignore
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # type: ignore
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    notes = models.TextField(null=True, blank=True)
    is_refunded = models.BooleanField(default=False)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-sale_date']
    
    def __str__(self):
        return f"Sale #{self.id} - {self.total_amount}"

class SaleItem(models.Model):
    objects = BusinessSpecificManager()
    # Add business relationship for multi-tenancy
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='sale_items', null=True)
    
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

class Refund(models.Model):
    objects = BusinessSpecificManager()
    # Add business relationship for multi-tenancy
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='refunds', null=True)
    
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    reason = models.TextField()
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    refund_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Refund for Sale #{self.sale.id}"