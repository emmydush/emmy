from django.db import models
from .middleware import get_current_business

class BusinessSpecificManager(models.Manager):
    """
    Custom manager that automatically filters objects by the current business context.
    This is used for multi-tenancy to ensure users only see data from their business.
    """
    
    def get_queryset(self):
        """
        Override get_queryset to filter by business context.
        """
        queryset = super().get_queryset()
        current_business = get_current_business()
        if current_business:
            # Check if the model has a direct business field
            if hasattr(self.model, 'business'):
                return queryset.filter(business=current_business)
            # Check if the model has a purchase_order relationship (for PurchaseItem)
            elif hasattr(self.model, 'purchase_order'):
                return queryset.filter(purchase_order__business=current_business)
            # Check if the model has a product relationship that can lead to business
            elif hasattr(self.model, 'product'):
                return queryset.filter(product__business=current_business)
            # Check if the model has a supplier relationship that can lead to business
            elif hasattr(self.model, 'supplier'):
                return queryset.filter(supplier__business=current_business)
            # Check if the model has a customer relationship that can lead to business
            elif hasattr(self.model, 'customer'):
                return queryset.filter(customer__business=current_business)
            else:
                # If no recognizable relationship to business, return empty queryset
                return queryset.none()
        # If no business context, return empty queryset to prevent data leakage
        return queryset.none()
    
    def business_specific(self):
        """
        Return a queryset filtered by the current business context.
        This method is used throughout the application to ensure multi-tenancy.
        """
        return self.get_queryset()
    
    def for_business(self, business):
        """
        Filter objects by a specific business.
        """
        # Check if the model has a direct business field
        if hasattr(self.model, 'business'):
            return self.get_queryset().filter(business=business)
        # Check if the model has a purchase_order relationship (for PurchaseItem)
        elif hasattr(self.model, 'purchase_order'):
            return self.get_queryset().filter(purchase_order__business=business)
        # Check if the model has a product relationship that can lead to business
        elif hasattr(self.model, 'product'):
            return self.get_queryset().filter(product__business=business)
        # Check if the model has a supplier relationship that can lead to business
        elif hasattr(self.model, 'supplier'):
            return self.get_queryset().filter(supplier__business=business)
        # Check if the model has a customer relationship that can lead to business
        elif hasattr(self.model, 'customer'):
            return self.get_queryset().filter(customer__business=business)
        else:
            # If no recognizable relationship to business, return empty queryset
            return self.get_queryset().none()