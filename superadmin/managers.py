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
            return queryset.filter(business=current_business)
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
        return self.get_queryset().filter(business=business)
