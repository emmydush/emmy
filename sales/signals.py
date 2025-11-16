from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from sales.models import SaleItem, Sale
from decimal import Decimal
import logging

# Set up logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=SaleItem)
@receiver(post_delete, sender=SaleItem)
def update_sale_total(sender, instance, **kwargs):
    """
    Update the sale total when a sale item is created, updated, or deleted.
    This ensures the sale total is always in sync with its items.
    """
    try:
        # Get the related sale
        sale = instance.sale
        
        # Recalculate the sale subtotal based on all items
        subtotal = Decimal('0.00')
        for item in sale.items.all():
            subtotal += item.total_price
            
        # Update the sale totals
        sale.subtotal = subtotal
        sale.total_amount = subtotal + sale.tax - sale.discount
        
        # Save the sale without triggering signals to avoid recursion
        sale.save(update_fields=['subtotal', 'total_amount'])
        
        logger.info(f"Updated sale #{sale.id} total to {sale.total_amount}")
        
    except Exception as e:
        # Log the error but don't fail the operation
        logger.error(f"Error updating sale total: {str(e)}")