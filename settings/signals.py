from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .utils import log_activity
from .models import AuditLog
import json

User = get_user_model()


# Product model tracking
@receiver(post_save, sender="products.Product")
def log_product_save(sender, instance, created, **kwargs):
    """Log product creation or update"""
    # Get the current user from thread local storage or request context
    user = getattr(instance, "_audit_user", None)

    if created:
        action = "CREATE"
        message = f"Product '{instance.name}' was created with SKU: {instance.sku}"
    else:
        action = "UPDATE"
        message = f"Product '{instance.name}' was updated"

    # Add details about what changed
    if hasattr(instance, "_changed_fields"):
        changes = []
        for field, (old_value, new_value) in instance._changed_fields.items():
            changes.append(f"{field}: {old_value} → {new_value}")
        if changes:
            message += f"\nChanges: {', '.join(changes)}"

    log_activity(
        user=user,
        action=action,
        model_name="Product",
        object_id=instance.pk,
        object_repr=str(instance),
        change_message=message,
    )


@receiver(post_delete, sender="products.Product")
def log_product_delete(sender, instance, **kwargs):
    """Log product deletion"""
    user = getattr(instance, "_audit_user", None)

    log_activity(
        user=user,
        action="DELETE",
        model_name="Product",
        object_id=instance.pk,
        object_repr=str(instance),
        change_message=f"Product '{instance.name}' was deleted",
    )


# Purchase Order tracking
@receiver(post_save, sender="purchases.PurchaseOrder")
def log_purchase_order_save(sender, instance, created, **kwargs):
    """Log purchase order creation or update"""
    user = getattr(instance, "_audit_user", None)

    if created:
        action = "CREATE"
        message = f"Purchase Order for supplier '{instance.supplier.name}' was created"
    else:
        action = "UPDATE"
        message = (
            f"Purchase Order #{instance.pk} was updated (Status: {instance.status})"
        )

    log_activity(
        user=user,
        action=action,
        model_name="PurchaseOrder",
        object_id=instance.pk,
        object_repr=str(instance),
        change_message=message,
    )


@receiver(post_delete, sender="purchases.PurchaseOrder")
def log_purchase_order_delete(sender, instance, **kwargs):
    """Log purchase order deletion"""
    user = getattr(instance, "_audit_user", None)

    log_activity(
        user=user,
        action="DELETE",
        model_name="PurchaseOrder",
        object_id=instance.pk,
        object_repr=str(instance),
        change_message=f"Purchase Order #{instance.pk} for supplier '{instance.supplier.name}' was deleted",
    )


# Purchase Item tracking
@receiver(post_save, sender="purchases.PurchaseItem")
def log_purchase_item_save(sender, instance, created, **kwargs):
    """Log purchase item creation or update"""
    user = getattr(instance, "_audit_user", None)

    if created:
        action = "CREATE"
        message = f"Added {instance.quantity} x '{instance.product.name}' to Purchase Order #{instance.purchase_order.pk}"
    else:
        action = "UPDATE"
        message = f"Updated item '{instance.product.name}' in Purchase Order #{instance.purchase_order.pk}"
        if hasattr(instance, "received_quantity"):
            message += f" (Received: {instance.received_quantity}/{instance.quantity})"

    log_activity(
        user=user,
        action=action,
        model_name="PurchaseItem",
        object_id=instance.pk,
        object_repr=str(instance),
        change_message=message,
    )


@receiver(post_delete, sender="purchases.PurchaseItem")
def log_purchase_item_delete(sender, instance, **kwargs):
    """Log purchase item deletion"""
    user = getattr(instance, "_audit_user", None)

    log_activity(
        user=user,
        action="DELETE",
        model_name="PurchaseItem",
        object_id=instance.pk,
        object_repr=str(instance),
        change_message=f"Removed item '{instance.product.name}' from Purchase Order #{instance.purchase_order.pk}",
    )


# Sale tracking
@receiver(post_save, sender="sales.Sale")
def log_sale_save(sender, instance, created, **kwargs):
    """Log sale creation or update"""
    user = getattr(instance, "_audit_user", None)

    if created:
        action = "CREATE"
        message = f"Sale created with total amount: {instance.total_amount}"
    else:
        action = "UPDATE"
        message = f"Sale #{instance.pk} was updated (Total: {instance.total_amount})"
        if instance.is_refunded:
            message += " - REFUNDED"

    log_activity(
        user=user,
        action=action,
        model_name="Sale",
        object_id=instance.pk,
        object_repr=str(instance),
        change_message=message,
    )


@receiver(post_delete, sender="sales.Sale")
def log_sale_delete(sender, instance, **kwargs):
    """Log sale deletion"""
    user = getattr(instance, "_audit_user", None)

    log_activity(
        user=user,
        action="DELETE",
        model_name="Sale",
        object_id=instance.pk,
        object_repr=str(instance),
        change_message=f"Sale #{instance.pk} with total amount {instance.total_amount} was deleted",
    )


# Expense tracking
@receiver(post_save, sender="expenses.Expense")
def log_expense_save(sender, instance, created, **kwargs):
    """Log expense creation or update"""
    user = getattr(instance, "_audit_user", None)

    if created:
        action = "CREATE"
        message = (
            f"Expense of {instance.amount} for '{instance.category.name}' was created"
        )
    else:
        action = "UPDATE"
        message = f"Expense #{instance.pk} of {instance.amount} for '{instance.category.name}' was updated"

    log_activity(
        user=user,
        action=action,
        model_name="Expense",
        object_id=instance.pk,
        object_repr=str(instance),
        change_message=message,
    )


@receiver(post_delete, sender="expenses.Expense")
def log_expense_delete(sender, instance, **kwargs):
    """Log expense deletion"""
    user = getattr(instance, "_audit_user", None)

    log_activity(
        user=user,
        action="DELETE",
        model_name="Expense",
        object_id=instance.pk,
        object_repr=str(instance),
        change_message=f"Expense #{instance.pk} of {instance.amount} for '{instance.category.name}' was deleted",
    )


# User tracking
@receiver(post_save, sender=User)
def log_user_save(sender, instance, created, **kwargs):
    """Log user creation or update"""
    user = getattr(instance, "_audit_user", None)

    if created:
        action = "CREATE"
        message = f"User '{instance.username}' was created"
    else:
        action = "UPDATE"
        message = f"User '{instance.username}' was updated"

    log_activity(
        user=user,
        action=action,
        model_name="User",
        object_id=instance.pk,
        object_repr=str(instance),
        change_message=message,
    )


@receiver(post_delete, sender=User)
def log_user_delete(sender, instance, **kwargs):
    """Log user deletion"""
    user = getattr(instance, "_audit_user", None)

    log_activity(
        user=user,
        action="DELETE",
        model_name="User",
        object_id=instance.pk,
        object_repr=str(instance),
        change_message=f"User '{instance.username}' was deleted",
    )
