from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from typing import TYPE_CHECKING
from .models import PurchaseOrder, PurchaseItem
from .forms import PurchaseOrderForm, PurchaseItemFormSet
from products.models import Product
from authentication.utils import check_user_permission


@login_required
def purchase_order_list(request):
    purchase_orders = PurchaseOrder.objects.business_specific().all()
    return render(request, "purchases/list.html", {"purchase_orders": purchase_orders})


@login_required
def purchase_order_create(request):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_create"
    ):
        messages.error(request, "You do not have permission to create purchase orders.")
        return redirect("purchases:list")

    # Get the current business from the request
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    if request.method == "POST":
        form = PurchaseOrderForm(request.POST)
        formset = PurchaseItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            if not current_business:
                messages.error(
                    request,
                    "No business context found. Please select a business before creating purchase orders.",
                )
                return render(
                    request,
                    "purchases/form.html",
                    {
                        "form": form,
                        "formset": formset,
                        "title": "Create Purchase Order",
                    },
                )

            # Save the purchase order with business context
            purchase_order = form.save(commit=False)
            purchase_order.business = current_business
            # Set the order_date to today if not provided
            if not purchase_order.order_date:
                from django.utils import timezone

                purchase_order.order_date = timezone.now().date()
            purchase_order.save()

            # Save the formset instances
            instances = formset.save(commit=False)
            for instance in instances:
                instance.purchase_order = purchase_order
                instance.save()
            # Delete any instances marked for deletion
            for obj in formset.deleted_objects:
                obj.delete()
            # Note: total_amount is a calculated property, so we don't need to set it
            purchase_order.save()
            messages.success(request, "Purchase order created successfully!")
            return redirect("purchases:detail", pk=purchase_order.pk)
    else:
        if not current_business:
            messages.error(
                request,
                "No business context found. Please select a business before creating purchase orders.",
            )
            return redirect("business_selection")
        form = PurchaseOrderForm()
        formset = PurchaseItemFormSet()

    return render(
        request,
        "purchases/form.html",
        {"form": form, "formset": formset, "title": "Create Purchase Order"},
    )


@login_required
def purchase_order_detail(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder.objects.business_specific(), pk=pk)
    return render(request, "purchases/detail.html", {"purchase_order": purchase_order})


@login_required
def purchase_order_update(request, pk):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_edit"
    ):
        messages.error(request, "You do not have permission to edit purchase orders.")
        return redirect("purchases:list")

    purchase_order = get_object_or_404(PurchaseOrder.objects.business_specific(), pk=pk)

    # Get the current business from the request
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    if request.method == "POST":
        form = PurchaseOrderForm(request.POST, instance=purchase_order)
        formset = PurchaseItemFormSet(request.POST, instance=purchase_order)
        if form.is_valid() and formset.is_valid():
            if not current_business:
                messages.error(
                    request,
                    "No business context found. Please select a business before updating purchase orders.",
                )
                return render(
                    request,
                    "purchases/form.html",
                    {
                        "form": form,
                        "formset": formset,
                        "title": "Update Purchase Order",
                        "purchase_order": purchase_order,
                    },
                )

            # Save the purchase order with business context
            purchase_order = form.save(commit=False)
            purchase_order.business = current_business
            purchase_order.save()

            # Save the formset instances
            instances = formset.save(commit=False)
            for instance in instances:
                instance.purchase_order = purchase_order
                instance.save()
            # Delete any instances marked for deletion
            for obj in formset.deleted_objects:
                obj.delete()
            # Note: total_amount is a calculated property, so we don't need to set it
            purchase_order.save()
            messages.success(request, "Purchase order updated successfully!")
            return redirect("purchases:detail", pk=purchase_order.pk)
    else:
        if not current_business:
            messages.error(
                request,
                "No business context found. Please select a business before updating purchase orders.",
            )
            return redirect("business_selection")
        form = PurchaseOrderForm(instance=purchase_order)
        formset = PurchaseItemFormSet(instance=purchase_order)

    return render(
        request,
        "purchases/form.html",
        {
            "form": form,
            "formset": formset,
            "title": "Update Purchase Order",
            "purchase_order": purchase_order,
        },
    )


@login_required
def purchase_order_delete(request, pk):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_delete"
    ):
        messages.error(request, "You do not have permission to delete purchase orders.")
        return redirect("purchases:list")

    purchase_order = get_object_or_404(PurchaseOrder.objects.business_specific(), pk=pk)

    if request.method == "POST":
        purchase_order.delete()
        messages.success(request, "Purchase order deleted successfully!")
        return redirect("purchases:list")

    return render(
        request, "purchases/confirm_delete.html", {"purchase_order": purchase_order}
    )


@login_required
def receive_items(request, pk):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_edit"
    ):
        messages.error(
            request, "You do not have permission to receive items for purchase orders."
        )
        return redirect("purchases:list")

    purchase_order = get_object_or_404(PurchaseOrder.objects.business_specific(), pk=pk)

    if request.method == "POST":
        # Process received items
        # The 'items' attribute is created by Django's related_name feature
        for item in purchase_order.items.all():  # type: ignore
            received_qty = request.POST.get(f"received_{item.pk}", 0)
            try:
                received_qty = float(received_qty)
            except ValueError:
                received_qty = 0

            if received_qty > 0:
                # Update received quantity
                # The stock will be automatically updated by signals
                item.received_quantity += received_qty
                item.save()

        # Update purchase order status
        # The 'items' attribute is created by Django's related_name feature
        if all(item.is_fully_received for item in purchase_order.items.all()):  # type: ignore
            purchase_order.status = "received"
        else:
            purchase_order.status = "partially_received"
        purchase_order.save()

        messages.success(request, "Items received successfully!")
        return redirect("purchases:detail", pk=purchase_order.pk)

    return render(request, "purchases/receive.html", {"purchase_order": purchase_order})
