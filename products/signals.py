from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from sales.models import SaleItem
from purchases.models import PurchaseItem
from products.models import Product, StockMovement
from notifications.models import Notification
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Store original received_quantity values to calculate differences
original_received_quantities = {}


@receiver(pre_save, sender=PurchaseItem)
def store_original_received_quantity(sender, instance, **kwargs):
    """
    Store the original received_quantity before saving a PurchaseItem
    """
    if instance.pk:
        try:
            old_instance = PurchaseItem.objects.get(pk=instance.pk)
            original_received_quantities[instance.pk] = old_instance.received_quantity
        except PurchaseItem.DoesNotExist:
            pass


@receiver(post_save, sender=SaleItem)
def update_product_stock_on_sale(sender, instance, created, **kwargs):
    """
    Update product stock when a sale item is created or updated.
    Only reduce stock when the sale item is first created.
    """
    logger.info(f"Signal triggered for SaleItem {instance.id}, created: {created}")

    if created:
        try:
            with transaction.atomic():  # type: ignore
                # Handle product variants
                if instance.is_product_variant and instance.product_variant:
                    product = instance.product_variant
                    product_parent = instance.product_variant.product
                    logger.info(
                        f"Updating stock for product variant {product.name} (ID: {product.id})"
                    )
                else:
                    product = instance.product
                    product_parent = instance.product
                    logger.info(
                        f"Updating stock for product {product.name} (ID: {product.id})"
                    )
                
                logger.info(
                    f"Current stock: {product.quantity}, Quantity sold: {instance.quantity}"
                )

                # Track the stock movement before updating
                previous_quantity = product.quantity
                # Convert to the same type to avoid type errors
                from decimal import Decimal

                quantity_sold = Decimal(str(instance.quantity))
                new_quantity = previous_quantity - quantity_sold

                # Track stock movement for analysis
                StockMovement.objects.create(
                    business=product.business,
                    product=product_parent,  # Always reference the parent product
                    movement_type="sale",
                    quantity=quantity_sold,
                    previous_quantity=previous_quantity,
                    new_quantity=new_quantity,
                    reference_id=str(instance.sale.id),
                    reference_model="Sale",
                    created_by=(
                        instance.sale.created_by
                        if hasattr(instance.sale, "created_by")
                        else None
                    ),
                )

                # Reduce product quantity by the sold amount
                product.quantity = new_quantity
                product.save()

                logger.info(f"New stock after sale: {product.quantity}")

                # Check if product is now low stock
                if product.quantity <= product.reorder_level:
                    # Create low stock notification for users in the same business
                    Notification.create_for_all_users(
                        title=f"Low Stock Alert: {product.name}",
                        message=f'The product "{product.name}" is low on stock after a sale. Current quantity: {product.quantity}, Reorder level: {product.reorder_level}',
                        notification_type="low_stock",
                        related_product=product_parent,  # Reference the parent product
                    )
        except Exception as e:
            # Log the error or handle it appropriately
            logger.error(f"Error updating product stock: {str(e)}")


@receiver(post_save, sender=PurchaseItem)
def update_product_stock_on_purchase_receive(sender, instance, created, **kwargs):
    """
    Update product stock when purchase items are received.
    For new items, no stock update is needed.
    For existing items, update stock based on received_quantity changes.
    """
    # For new items, no stock update is needed at creation
    if created:
        return

    # For existing items, calculate the difference in received quantity
    if instance.pk:
        try:
            # Get the original received_quantity
            original_quantity = original_received_quantities.get(instance.pk, 0)

            # Calculate the difference in received quantity
            quantity_difference = instance.received_quantity - original_quantity

            # Remove the stored original value
            if instance.pk in original_received_quantities:
                del original_received_quantities[instance.pk]

            if quantity_difference > 0:
                with transaction.atomic():  # type: ignore
                    # Handle product variants
                    if hasattr(instance, 'is_product_variant') and instance.is_product_variant and hasattr(instance, 'product_variant') and instance.product_variant:
                        product = instance.product_variant
                        product_parent = instance.product_variant.product
                    else:
                        product = instance.product
                        product_parent = instance.product

                    # Track the stock movement before updating
                    previous_quantity = product.quantity
                    # Convert to the same type to avoid type errors
                    from decimal import Decimal

                    quantity_received = Decimal(str(quantity_difference))
                    new_quantity = previous_quantity + quantity_received

                    # Track stock movement for analysis
                    StockMovement.objects.create(
                        business=product.business,
                        product=product_parent,  # Always reference the parent product
                        movement_type="purchase",
                        quantity=quantity_received,
                        previous_quantity=previous_quantity,
                        new_quantity=new_quantity,
                        reference_id=str(instance.purchase.id),
                        reference_model="Purchase",
                        created_by=(
                            instance.purchase.created_by
                            if hasattr(instance.purchase, "created_by")
                            else None
                        ),
                    )

                    # Increase product quantity by the received amount
                    product.quantity = new_quantity
                    product.save()
        except Exception as e:
            # Log the error or handle it appropriately
            logger.error(f"Error updating product stock on purchase receive: {e}")
            print(f"Error updating product stock on purchase receive: {e}")


@receiver(post_delete, sender=SaleItem)
def restore_product_stock_on_sale_delete(sender, instance, **kwargs):
    """
    Restore product stock when a sale item is deleted.
    """
    try:
        with transaction.atomic():  # type: ignore
            # Handle product variants
            if instance.is_product_variant and instance.product_variant:
                product = instance.product_variant
                product_parent = instance.product_variant.product
                logger.info(
                    f"Restoring stock for product variant {product.name} (ID: {product.id})"
                )
            else:
                product = instance.product
                product_parent = instance.product
                logger.info(
                    f"Restoring stock for product {product.name} (ID: {product.id})"
                )

            # Track the stock movement before updating
            previous_quantity = product.quantity
            # Convert to the same type to avoid type errors
            from decimal import Decimal

            quantity_restored = Decimal(str(instance.quantity))
            new_quantity = previous_quantity + quantity_restored

            # Track stock movement for analysis
            StockMovement.objects.create(
                business=product.business,
                product=product_parent,  # Always reference the parent product
                movement_type="sale",
                quantity=quantity_restored,
                previous_quantity=previous_quantity,
                new_quantity=new_quantity,
                reference_id=(
                    str(instance.sale.id)
                    if hasattr(instance, "sale")
                    else "deleted_sale"
                ),
                reference_model="Sale",
                created_by=None,  # No user context available for deletions
            )

            # Increase product quantity by the sold amount
            product.quantity = new_quantity
            product.save()
    except Exception as e:
        # Log the error or handle it appropriately
        logger.error(f"Error restoring product stock on sale delete: {e}")
        print(f"Error restoring product stock on sale delete: {e}")


@receiver(post_save, sender=Product)
def set_default_values_for_product(sender, instance, created, **kwargs):
    """
    Set default values for new products.
    """
    if created:
        # Ensure default values are set
        if instance.quantity is None:
            instance.quantity = 0
        if instance.reorder_level is None:
            instance.reorder_level = 0
        if instance.cost_price is None:
            instance.cost_price = 0
        if instance.selling_price is None:
            instance.selling_price = 0
        instance.save()
