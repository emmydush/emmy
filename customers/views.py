from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Customer
from .forms import CustomerForm
from superadmin.middleware import get_current_business
from authentication.utils import check_user_permission


@login_required
def customer_list(request):
    customers = Customer.objects.business_specific().filter(is_active=True)
    return render(request, "customers/list.html", {"customers": customers})


@login_required
def customer_create(request):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_create"
    ):
        messages.error(request, "You do not have permission to create customers.")
        return redirect("customers:list")

    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            # Get the current business from middleware
            current_business = get_current_business()
            if current_business:
                # Save the customer with the business context
                customer = form.save(commit=False)
                customer.business = current_business
                customer.save()
                messages.success(request, "Customer created successfully!")
                return redirect("customers:list")
            else:
                messages.error(
                    request, "No business context found. Please select a business."
                )
    else:
        form = CustomerForm()

    return render(
        request, "customers/form.html", {"form": form, "title": "Create Customer"}
    )


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer.objects.business_specific(), pk=pk)
    return render(request, "customers/detail.html", {"customer": customer})


@login_required
def customer_update(request, pk):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_edit"
    ):
        messages.error(request, "You do not have permission to edit customers.")
        return redirect("customers:list")

    customer = get_object_or_404(Customer.objects.business_specific(), pk=pk)

    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer updated successfully!")
            return redirect("customers:detail", pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)

    return render(
        request,
        "customers/form.html",
        {"form": form, "title": "Update Customer", "customer": customer},
    )


@login_required
def customer_delete(request, pk):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_delete"
    ):
        messages.error(request, "You do not have permission to delete customers.")
        return redirect("customers:list")

    customer = get_object_or_404(Customer.objects.business_specific(), pk=pk)

    if request.method == "POST":
        customer.is_active = False
        customer.save()
        messages.success(request, "Customer deleted successfully!")
        return redirect("customers:list")

    return render(request, "customers/confirm_delete.html", {"customer": customer})
