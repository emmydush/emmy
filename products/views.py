from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, F, Value
from django.db.models.query import QuerySet
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
from django.utils import timezone
from decimal import Decimal
import datetime
import qrcode
import csv
import io
from .models import Product, Category, Unit, StockAdjustment, StockAlert, StockMovement, ProductVariant, VariantAttribute, VariantAttributeValue, ProductVariantAttribute
from .forms import (
    ProductForm,
    CategoryForm,
    UnitForm,
    StockAdjustmentForm,
    StockAdjustmentApprovalForm,
    ProductVariantForm,
    VariantAttributeForm,
    VariantAttributeValueForm,
    ProductVariantAttributeForm,
)
from .utils import generate_product_qr_code
from authentication.utils import check_user_permission, require_permission


@login_required
def product_list(request):
    # Get search and filter parameters
    search_query = request.GET.get("search", "")
    category_id = request.GET.get("category", "")
    status = request.GET.get("status", "")

    # Start with all active products, filtered by business context
    products = (
        Product.objects.business_specific()
        .filter(is_active=True)
        .select_related("category", "unit")
    )

    # Apply search filter
    if search_query:
        # Build a single Q object with all search conditions to avoid type checking issues
        search_filter = (
            Q(name__icontains=search_query)
            | Q(sku__icontains=search_query)
            | Q(description__icontains=search_query)
        )
        products = products.filter(search_filter)

    # Apply category filter
    if category_id:
        products = products.filter(category_id=category_id)

    # Apply status filter
    if status:
        if status == "low_stock":
            products = products.filter(quantity__lte=F("reorder_level"))
        elif status == "active":
            products = products.filter(is_active=True)
        elif status == "inactive":
            products = products.filter(is_active=False)

    # Get categories for filter dropdown, filtered by business context
    categories = Category.objects.business_specific().all()

    context = {
        "products": products,
        "categories": categories,
        "search_query": search_query,
        "selected_category": category_id,
        "selected_status": status,
    }

    return render(request, "products/list.html", context)


@login_required
@require_http_methods(["GET"])
def product_search_ajax(request):
    """
    AJAX view for real-time product search
    Returns JSON response with matching products
    """
    search_query = request.GET.get("q", "")

    if len(search_query) < 1:
        return JsonResponse({"products": []})

    # Build a single Q object with all search conditions to avoid type checking issues
    search_filter = (
        Q(name__icontains=search_query)
        | Q(sku__icontains=search_query)
        | Q(description__icontains=search_query)
    )

    # Search for products matching the query, filtered by business context
    products = (
        Product.objects.business_specific()
        .filter(search_filter)
        .filter(is_active=True)[:10]
    )  # Limit to 10 results for performance

    # Format products for JSON response
    product_list = []
    for product in products:
        product_list.append(
            {
                "id": product.id,
                "name": product.name,
                "sku": product.sku,
                "selling_price": float(product.selling_price),
                "quantity": float(product.quantity),
                "unit": product.unit.symbol if product.unit else "",
                "category": product.category.name if product.category else "",
            }
        )

    return JsonResponse({"products": product_list})


@login_required
@require_http_methods(["GET"])
def product_json(request, pk):
    """
    API endpoint to return product details as JSON
    """
    # Get current business from middleware
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    if not current_business:
        return JsonResponse({"error": "No business context found"}, status=400)

    try:
        # Make sure the product belongs to the current business
        product = get_object_or_404(
            Product.objects.filter(business=current_business), pk=pk, is_active=True
        )
        return JsonResponse(
            {
                "id": product.id,
                "name": product.name,
                "sku": product.sku,
                "cost_price": float(product.cost_price),
                "selling_price": float(product.selling_price),
                "quantity": float(product.quantity),
                "unit": product.unit.symbol if product.unit else "",
                "category": product.category.name if product.category else "",
            }
        )
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)


@login_required
def product_create(request):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_create"
    ):
        messages.error(request, "You do not have permission to create products.")
        return redirect("products:list")

    # Get the current business from the request
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, business=current_business)
        if form.is_valid():
            if current_business:
                try:
                    # Save the product with business context
                    product = form.save(commit=False)
                    product.business = current_business
                    product.save()
                    messages.success(request, "Product created successfully!")
                    return redirect("products:list")
                except IntegrityError as e:
                    if "products_product_business_id_sku_cee6e09f_uniq" in str(e):
                        messages.error(
                            request,
                            "A product with this SKU already exists for your business. Please use a different SKU.",
                        )
                    else:
                        messages.error(
                            request,
                            f"An error occurred while creating the product: {str(e)}",
                        )
            else:
                messages.error(
                    request,
                    "No business context found. Please select a business before creating products.",
                )
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = ProductForm(business=current_business)

    return render(
        request, "products/form.html", {"form": form, "title": "Create Product"}
    )


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.business_specific(), pk=pk)

    # Generate QR code for the product
    qr_buffer = generate_product_qr_code(product)

    context = {
        "product": product,
        "qr_code_data": qr_buffer.getvalue() if qr_buffer else None,
        "MEDIA_URL": settings.MEDIA_URL,
    }

    return render(request, "products/detail.html", context)


@login_required
def product_update(request, pk):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_edit"
    ):
        messages.error(request, "You do not have permission to edit products.")
        return redirect("products:list")

    product = get_object_or_404(Product.objects.business_specific(), pk=pk)

    # Get the current business from the request
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    if request.method == "POST":
        form = ProductForm(
            request.POST, request.FILES, instance=product, business=current_business
        )
        if form.is_valid():
            if current_business:
                # Save the product with business context
                product = form.save(commit=False)
                product.business = current_business
                product.save()
                messages.success(request, "Product updated successfully!")
                return redirect("products:detail", pk=product.pk)
            else:
                messages.error(
                    request,
                    "No business context found. Please select a business before updating products.",
                )
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = ProductForm(instance=product, business=current_business)

    return render(
        request,
        "products/form.html",
        {"form": form, "title": "Update Product", "product": product},
    )


@login_required
def product_delete(request, pk):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_delete"
    ):
        messages.error(request, "You do not have permission to delete products.")
        return redirect("products:list")

    product = get_object_or_404(Product.objects.business_specific(), pk=pk)

    if request.method == "POST":
        product.is_active = False
        product.save()
        messages.success(request, "Product deleted successfully!")
        return redirect("products:list")

    return render(request, "products/confirm_delete.html", {"product": product})


@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, "products/categories/list.html", {"categories": categories})


@login_required
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            # Set the business context for the category
            category = form.save(commit=False)
            # Get the current business from the request
            from superadmin.middleware import get_current_business

            current_business = get_current_business()
            if current_business:
                category.business = current_business
                category.save()
                messages.success(request, "Category created successfully!")
                return redirect("products:category_list")
            else:
                messages.error(
                    request,
                    "No business context found. Please select a business before creating categories.",
                )
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = CategoryForm()

    return render(
        request,
        "products/categories/form.html",
        {"form": form, "title": "Create Category"},
    )


@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            # Set the business context for the category
            category = form.save(commit=False)
            # Get the current business from the request
            from superadmin.middleware import get_current_business

            current_business = get_current_business()
            if current_business:
                category.business = current_business
                category.save()
                messages.success(request, "Category updated successfully!")
                return redirect("products:category_list")
            else:
                messages.error(
                    request,
                    "No business context found. Please select a business before updating categories.",
                )
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = CategoryForm(instance=category)

    return render(
        request,
        "products/categories/form.html",
        {"form": form, "title": "Update Category", "category": category},
    )


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted successfully!")
        return redirect("products:category_list")

    return render(
        request, "products/categories/confirm_delete.html", {"category": category}
    )


@login_required
def unit_list(request):
    units = Unit.objects.all()
    return render(request, "products/units/list.html", {"units": units})


@login_required
def unit_create(request):
    if request.method == "POST":
        form = UnitForm(request.POST)
        if form.is_valid():
            # Set the business context for the unit
            unit = form.save(commit=False)
            # Get the current business from the request
            from superadmin.middleware import get_current_business

            current_business = get_current_business()
            if current_business:
                unit.business = current_business
                unit.save()
                messages.success(request, "Unit created successfully!")
                return redirect("products:unit_list")
            else:
                messages.error(
                    request,
                    "No business context found. Please select a business before creating units.",
                )
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = UnitForm()

    return render(
        request, "products/units/form.html", {"form": form, "title": "Create Unit"}
    )


@login_required
def bulk_upload(request):
    if request.method == "POST":
        if "csv_file" in request.FILES:
            csv_file = request.FILES["csv_file"]

            # Check if file is CSV
            if not csv_file.name.endswith(".csv"):
                messages.error(request, "Please upload a CSV file.")
                return redirect("products:bulk_upload")

            # Process the CSV file
            try:
                decoded_file = csv_file.read().decode("utf-8")
                io_string = io.StringIO(decoded_file)
                reader = csv.reader(io_string, delimiter=",")

                # Skip header row
                next(reader)

                success_count = 0
                update_count = 0
                error_count = 0
                errors = []

                for i, row in enumerate(reader):
                    try:
                        # Extract data from CSV row
                        # Expected columns: name, sku, barcode, category_name, unit_name,
                        # description, cost_price, selling_price, quantity, reorder_level, expiry_date
                        if len(row) < 11:
                            errors.append(f"Row {i+2}: Insufficient columns")
                            error_count += 1
                            continue

                        (
                            name,
                            sku,
                            barcode,
                            category_name,
                            unit_name,
                            description,
                            cost_price,
                            selling_price,
                            quantity,
                            reorder_level,
                            expiry_date,
                        ) = row

                        # Validate required fields
                        if not name or not sku or not category_name or not unit_name:
                            errors.append(
                                f"Row {i+2}: Missing required fields (name, sku, category, unit)"
                            )
                            error_count += 1
                            continue

                        # Get the current business from the request
                        from superadmin.middleware import get_current_business

                        current_business = get_current_business()
                        if not current_business:
                            errors.append(f"Row {i+2}: No business context found")
                            error_count += 1
                            continue

                        # Get or create category
                        category, _ = Category.objects.get_or_create(
                            business=current_business,
                            name=category_name,
                            defaults={"description": f"Category for {category_name}"},
                        )

                        # Get or create unit
                        unit, _ = Unit.objects.get_or_create(
                            business=current_business,
                            name=unit_name,
                            defaults={"symbol": unit_name[:3].upper()},
                        )

                        # Handle empty values
                        barcode = barcode if barcode else None
                        description = description if description else ""
                        
                        # Parse numeric values
                        try:
                            cost_price = Decimal(cost_price) if cost_price else Decimal("0")
                        except:
                            cost_price = Decimal("0")
                            
                        try:
                            selling_price = Decimal(selling_price) if selling_price else Decimal("0")
                        except:
                            selling_price = Decimal("0")
                            
                        try:
                            quantity = Decimal(quantity) if quantity else Decimal("0")
                        except:
                            quantity = Decimal("0")
                            
                        try:
                            reorder_level = Decimal(reorder_level) if reorder_level else Decimal("0")
                        except:
                            reorder_level = Decimal("0")

                        # Parse expiry date
                        parsed_expiry_date = None
                        if expiry_date:
                            try:
                                parsed_expiry_date = datetime.datetime.strptime(expiry_date, "%Y-%m-%d").date()
                            except ValueError:
                                # Try other common date formats
                                try:
                                    parsed_expiry_date = datetime.datetime.strptime(expiry_date, "%d/%m/%Y").date()
                                except ValueError:
                                    try:
                                        parsed_expiry_date = datetime.datetime.strptime(expiry_date, "%m/%d/%Y").date()
                                    except ValueError:
                                        parsed_expiry_date = None

                        # Check if product with this SKU already exists
                        existing_product = Product.objects.filter(
                            business=current_business, sku=sku
                        ).first()

                        if existing_product:
                            # Update existing product
                            existing_product.name = name
                            existing_product.barcode = barcode
                            existing_product.category = category
                            existing_product.unit = unit
                            existing_product.description = description
                            existing_product.cost_price = cost_price
                            existing_product.selling_price = selling_price
                            existing_product.quantity = quantity
                            existing_product.reorder_level = reorder_level
                            existing_product.expiry_date = parsed_expiry_date
                            existing_product.save()
                            update_count += 1
                        else:
                            # Create new product
                            Product.objects.create(
                                business=current_business,
                                name=name,
                                sku=sku,
                                barcode=barcode,
                                category=category,
                                unit=unit,
                                description=description,
                                cost_price=cost_price,
                                selling_price=selling_price,
                                quantity=quantity,
                                reorder_level=reorder_level,
                                expiry_date=parsed_expiry_date,
                            )
                            success_count += 1

                    except Exception as e:
                        errors.append(f"Row {i+2}: {str(e)}")
                        error_count += 1

                # Prepare success message
                success_message = ""
                if success_count > 0:
                    success_message += f"Successfully imported {success_count} new products."
                if update_count > 0:
                    success_message += f" Updated {update_count} existing products."
                
                if success_message:
                    messages.success(request, success_message.strip())
                    
                if error_count > 0:
                    error_message = f"Failed to process {error_count} rows."
                    if errors:
                        error_message += " Errors: " + "; ".join(errors[:5])  # Show first 5 errors
                        if len(errors) > 5:
                            error_message += f" ... and {len(errors) - 5} more."
                    messages.error(request, error_message)

            except Exception as e:
                messages.error(request, f"Error processing CSV file: {str(e)}")
        else:
            messages.error(request, "No file uploaded.")

        return redirect("products:bulk_upload")

    return render(request, "products/bulk_upload.html")


@login_required
def export_products_csv(request):
    # Create the HttpResponse object with the appropriate CSV header
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="products.csv"'

    writer = csv.writer(response)

    # Write header row
    writer.writerow(
        [
            "Name",
            "SKU",
            "Barcode",
            "Category",
            "Unit",
            "Description",
            "Cost Price",
            "Selling Price",
            "Quantity",
            "Reorder Level",
            "Expiry Date",
        ]
    )

    # Write data rows
    products = Product.objects.all().select_related("category", "unit")
    for product in products:
        writer.writerow(
            [
                product.name,
                product.sku,
                product.barcode or "",
                product.category.name,
                product.unit.name,
                product.description or "",
                product.cost_price,
                product.selling_price,
                product.quantity,
                product.reorder_level,
                product.expiry_date or "",
            ]
        )

    return response


@login_required
def download_template(request):
    # Create the HttpResponse object with the appropriate CSV header
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="products_template.csv"'

    writer = csv.writer(response)

    # Write header row
    writer.writerow([
        "Name",
        "SKU",
        "Barcode",
        "Category",
        "Unit",
        "Description",
        "Cost Price",
        "Selling Price",
        "Quantity",
        "Reorder Level",
        "Expiry Date"
    ])

    # Write sample data rows
    sample_data = [
        [
            "iPhone 15 Pro",
            "IP15PRO-256-BLK",
            "1234567890128",
            "Electronics",
            "Piece",
            "Apple iPhone 15 Pro 256GB Black",
            "899.99",
            "1099.99",
            "25",
            "5",
            "2026-12-31"
        ],
        [
            "Samsung Galaxy Tab S9",
            "S9TAB-128-WHT",
            "2345678901234",
            "Electronics",
            "Piece",
            "Samsung Galaxy Tab S9 128GB White",
            "599.99",
            "749.99",
            "15",
            "3",
            "2026-11-30"
        ],
        [
            "Office Chair",
            "OFCCHR-BLK-LRG",
            "3456789012345",
            "Furniture",
            "Piece",
            "Ergonomic Office Chair Black Large",
            "149.99",
            "199.99",
            "8",
            "2",
            ""
        ]
    ]

    # Write sample data rows
    for row in sample_data:
        writer.writerow(row)

    return response


@login_required
def request_stock_adjustment(request):
    """View for requesting stock adjustments"""
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    if request.method == "POST":
        form = StockAdjustmentForm(request.POST, business=current_business)
        if form.is_valid():
            adjustment = form.save(commit=False)
            adjustment.business = current_business
            adjustment.requested_by = request.user
            adjustment.save()
            messages.success(
                request, "Stock adjustment request submitted successfully!"
            )
            return redirect("products:stock_adjustment_list")
    else:
        form = StockAdjustmentForm(business=current_business)

    return render(
        request,
        "products/request_stock_adjustment.html",
        {"form": form, "business": current_business},
    )


@login_required
def stock_adjustment_list(request):
    """View for listing stock adjustment requests"""
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    # Get filter parameters
    status_filter = request.GET.get("status", "")
    type_filter = request.GET.get("type", "")
    product_filter = request.GET.get("product", "")

    # Start with all adjustments for this business
    adjustments = StockAdjustment.objects.filter(business=current_business)

    # Apply filters
    if status_filter:
        adjustments = adjustments.filter(status=status_filter)
    if type_filter:
        adjustments = adjustments.filter(adjustment_type=type_filter)
    if product_filter:
        adjustments = adjustments.filter(product__id=product_filter)

    # Paginate the adjustments
    from django.core.paginator import Paginator

    paginator = Paginator(adjustments, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get filter options
    products = Product.objects.filter(business=current_business).order_by("name")

    context = {
        "page_obj": page_obj,
        "products": products,
        "status_filter": status_filter,
        "type_filter": type_filter,
        "product_filter": product_filter,
    }

    return render(request, "products/stock_adjustment_list.html", context)


@login_required
def approve_stock_adjustment(request, pk):
    """View for approving/rejecting stock adjustments"""
    from superadmin.middleware import get_current_business
    from authentication.utils import check_user_permission

    # Check if user has permission to approve stock adjustments
    # Only admin, manager, and stock_manager roles can approve/reject
    allowed_roles = ['admin', 'manager', 'stock_manager']
    if request.user.role.lower() not in allowed_roles and not check_user_permission(request.user, 'can_edit'):
        messages.error(request, "You do not have permission to approve or reject stock adjustment requests.")
        return redirect("products:stock_adjustment_list")

    current_business = get_current_business()

    adjustment = get_object_or_404(StockAdjustment, pk=pk, business=current_business)

    # Only allow approval/rejection of pending requests
    if adjustment.status != "pending":
        messages.error(request, "This adjustment request has already been processed.")
        return redirect("products:stock_adjustment_list")

    if request.method == "POST":
        form = StockAdjustmentApprovalForm(request.POST, instance=adjustment)
        if form.is_valid():
            adjustment = form.save(commit=False)
            adjustment.approved_by = request.user
            adjustment.approved_at = timezone.now()
            adjustment.save()

            # If approved, process the stock adjustment
            if adjustment.status == "approved":
                # Update product quantity
                if adjustment.adjustment_type == "in":
                    adjustment.product.quantity += adjustment.quantity
                else:  # out
                    adjustment.product.quantity -= adjustment.quantity
                adjustment.product.save()

                messages.success(
                    request,
                    f"Stock adjustment approved and processed successfully! {adjustment.product.name} quantity updated.",
                )
            elif adjustment.status == "rejected":
                messages.success(request, "Stock adjustment request rejected.")

            return redirect("products:stock_adjustment_list")
    else:
        form = StockAdjustmentApprovalForm(instance=adjustment)

    return render(
        request,
        "products/approve_stock_adjustment.html",
        {
            "form": form,
            "adjustment": adjustment,
        },
    )


@login_required
def stock_adjustment_detail(request, pk):
    """View for viewing stock adjustment details"""
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    adjustment = get_object_or_404(StockAdjustment, pk=pk, business=current_business)

    return render(
        request,
        "products/stock_adjustment_detail.html",
        {
            "adjustment": adjustment,
        },
    )


@login_required
def stock_alerts_list(request):
    """View for listing stock alerts"""
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    # Get filter parameters
    alert_type_filter = request.GET.get("alert_type", "")
    severity_filter = request.GET.get("severity", "")
    status_filter = request.GET.get("status", "unresolved")

    # Start with all alerts for this business
    alerts = StockAlert.objects.filter(business=current_business)

    # Apply filters
    if alert_type_filter:
        alerts = alerts.filter(alert_type=alert_type_filter)
    if severity_filter:
        alerts = alerts.filter(severity=severity_filter)
    if status_filter == "resolved":
        alerts = alerts.filter(is_resolved=True)
    elif status_filter == "unresolved":
        alerts = alerts.filter(is_resolved=False)

    # Paginate the alerts
    from django.core.paginator import Paginator

    paginator = Paginator(alerts, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "alert_type_filter": alert_type_filter,
        "severity_filter": severity_filter,
        "status_filter": status_filter,
    }

    return render(request, "products/stock_alerts_list.html", context)


@login_required
def resolve_stock_alert(request, pk):
    """View for resolving stock alerts"""
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    alert = get_object_or_404(StockAlert, pk=pk, business=current_business)

    if request.method == "POST":
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user
        alert.save()
        messages.success(request, "Stock alert marked as resolved!")
        return redirect("products:stock_alerts_list")

    return render(
        request,
        "products/resolve_stock_alert.html",
        {
            "alert": alert,
        },
    )


# This was mistakenly included - removing it


# Variant Management Views

@login_required
def product_variant_list(request, product_pk):
    """Display list of variants for a specific product"""
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_view"
    ):
        messages.error(request, "You do not have permission to view product variants.")
        return redirect("products:list")
    
    product = get_object_or_404(Product.objects.business_specific(), pk=product_pk)
    variants = product.variants.all()
    
    context = {
        "product": product,
        "variants": variants,
    }
    
    return render(request, "products/variants/list.html", context)


@login_required
def product_variant_create(request, product_pk):
    """Create a new variant for a specific product"""
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_create"
    ):
        messages.error(request, "You do not have permission to create product variants.")
        return redirect("products:list")
    
    product = get_object_or_404(Product.objects.business_specific(), pk=product_pk)
    
    # Get the current business from the request
    from superadmin.middleware import get_current_business
    current_business = get_current_business()
    
    if request.method == "POST":
        form = ProductVariantForm(request.POST, request.FILES, business=current_business, product=product)
        if form.is_valid():
            if current_business:
                try:
                    # Save the variant with business context
                    variant = form.save(commit=False)
                    variant.business = current_business
                    variant.product = product
                    variant.save()
                    
                    # Update the product's has_variants field
                    if not product.has_variants:
                        product.has_variants = True
                        product.save(update_fields=['has_variants'])
                    
                    messages.success(request, "Product variant created successfully!")
                    return redirect("products:variant_list", product_pk=product.pk)
                except IntegrityError as e:
                    if "products_productvariant_business_id_sku_key" in str(e):
                        messages.error(
                            request,
                            "A product variant with this SKU already exists for your business. Please use a different SKU.",
                        )
                    else:
                        messages.error(
                            request,
                            f"An error occurred while creating the product variant: {str(e)}",
                        )
            else:
                messages.error(
                    request,
                    "No business context found. Please select a business before creating product variants.",
                )
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = ProductVariantForm(business=current_business, product=product)
    
    context = {
        "form": form,
        "product": product,
        "title": "Create Product Variant",
    }
    
    return render(request, "products/variants/form.html", context)


@login_required
def product_variant_detail(request, pk):
    """Display details of a specific product variant"""
    variant = get_object_or_404(ProductVariant.objects.business_specific(), pk=pk)
    
    # Generate QR code for the variant
    qr_buffer = generate_product_qr_code(variant)
    
    context = {
        "variant": variant,
        "qr_code_data": qr_buffer.getvalue() if qr_buffer else None,
        "MEDIA_URL": settings.MEDIA_URL,
    }
    
    return render(request, "products/variants/detail.html", context)


@login_required
def product_variant_update(request, pk):
    """Update a specific product variant"""
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_edit"
    ):
        messages.error(request, "You do not have permission to edit product variants.")
        return redirect("products:list")
    
    variant = get_object_or_404(ProductVariant.objects.business_specific(), pk=pk)
    
    # Get the current business from the request
    from superadmin.middleware import get_current_business
    current_business = get_current_business()
    
    if request.method == "POST":
        form = ProductVariantForm(request.POST, request.FILES, instance=variant, business=current_business, product=variant.product)
        if form.is_valid():
            if current_business:
                # Save the variant with business context
                variant = form.save(commit=False)
                variant.business = current_business
                variant.save()
                messages.success(request, "Product variant updated successfully!")
                return redirect("products:variant_detail", pk=variant.pk)
            else:
                messages.error(
                    request,
                    "No business context found. Please select a business before updating product variants.",
                )
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = ProductVariantForm(instance=variant, business=current_business, product=variant.product)
    
    context = {
        "form": form,
        "variant": variant,
        "title": "Update Product Variant",
    }
    
    return render(request, "products/variants/form.html", context)


@login_required
def product_variant_delete(request, pk):
    """Delete a specific product variant"""
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_delete"
    ):
        messages.error(request, "You do not have permission to delete product variants.")
        return redirect("products:list")
    
    variant = get_object_or_404(ProductVariant.objects.business_specific(), pk=pk)
    product_pk = variant.product.pk
    product = variant.product
    
    if request.method == "POST":
        variant.is_active = False
        variant.save()
        
        # Check if this was the last variant for the product
        # If so, update the product's has_variants field
        if product.has_variants and not product.variants.filter(is_active=True).exists():
            product.has_variants = False
            product.save(update_fields=['has_variants'])
        
        messages.success(request, "Product variant deleted successfully!")
        return redirect("products:variant_list", product_pk=product_pk)
    
    context = {
        "variant": variant,
    }
    
    return render(request, "products/variants/confirm_delete.html", context)


# Variant Attribute Management Views

@login_required
def variant_attribute_list(request):
    """Display list of variant attributes"""
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_view"
    ):
        messages.error(request, "You do not have permission to view variant attributes.")
        return redirect("products:list")
    
    attributes = VariantAttribute.objects.business_specific().all()
    
    context = {
        "attributes": attributes,
    }
    
    return render(request, "products/variant_attributes/list.html", context)


@login_required
def variant_attribute_create(request):
    """Create a new variant attribute"""
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_create"
    ):
        messages.error(request, "You do not have permission to create variant attributes.")
        return redirect("products:list")
    
    # Get the current business from the request
    from superadmin.middleware import get_current_business
    current_business = get_current_business()
    
    if request.method == "POST":
        form = VariantAttributeForm(request.POST, business=current_business)
        if form.is_valid():
            if current_business:
                try:
                    # Save the attribute with business context
                    attribute = form.save(commit=False)
                    attribute.business = current_business
                    attribute.save()
                    messages.success(request, "Variant attribute created successfully!")
                    return redirect("products:variant_attribute_list")
                except IntegrityError as e:
                    messages.error(
                        request,
                        f"An error occurred while creating the variant attribute: {str(e)}",
                    )
            else:
                messages.error(
                    request,
                    "No business context found. Please select a business before creating variant attributes.",
                )
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = VariantAttributeForm(business=current_business)
    
    context = {
        "form": form,
        "title": "Create Variant Attribute",
    }
    
    return render(request, "products/variant_attributes/form.html", context)


@login_required
def variant_attribute_update(request, pk):
    """Update a specific variant attribute"""
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_edit"
    ):
        messages.error(request, "You do not have permission to edit variant attributes.")
        return redirect("products:list")
    
    attribute = get_object_or_404(VariantAttribute.objects.business_specific(), pk=pk)
    
    # Get the current business from the request
    from superadmin.middleware import get_current_business
    current_business = get_current_business()
    
    if request.method == "POST":
        form = VariantAttributeForm(request.POST, instance=attribute, business=current_business)
        if form.is_valid():
            if current_business:
                # Save the attribute with business context
                attribute = form.save(commit=False)
                attribute.business = current_business
                attribute.save()
                messages.success(request, "Variant attribute updated successfully!")
                return redirect("products:variant_attribute_list")
            else:
                messages.error(
                    request,
                    "No business context found. Please select a business before updating variant attributes.",
                )
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = VariantAttributeForm(instance=attribute, business=current_business)
    
    context = {
        "form": form,
        "attribute": attribute,
        "title": "Update Variant Attribute",
    }
    
    return render(request, "products/variant_attributes/form.html", context)


@login_required
def variant_attribute_delete(request, pk):
    """Delete a specific variant attribute"""
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_delete"
    ):
        messages.error(request, "You do not have permission to delete variant attributes.")
        return redirect("products:list")
    
    attribute = get_object_or_404(VariantAttribute.objects.business_specific(), pk=pk)
    
    if request.method == "POST":
        attribute.is_active = False
        attribute.save()
        messages.success(request, "Variant attribute deleted successfully!")
        return redirect("products:variant_attribute_list")
    
    context = {
        "attribute": attribute,
    }
    
    return render(request, "products/variant_attributes/confirm_delete.html", context)


# Variant Attribute Value Management Views

@login_required
def variant_attribute_value_list(request):
    """Display list of variant attribute values"""
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_view"
    ):
        messages.error(request, "You do not have permission to view variant attribute values.")
        return redirect("products:list")
    
    values = VariantAttributeValue.objects.business_specific().select_related('attribute')
    
    context = {
        "values": values,
    }
    
    return render(request, "products/variant_attribute_values/list.html", context)


@login_required
def variant_attribute_value_create(request):
    """Create a new variant attribute value"""
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_create"
    ):
        messages.error(request, "You do not have permission to create variant attribute values.")
        return redirect("products:list")
    
    # Get the current business from the request
    from superadmin.middleware import get_current_business
    current_business = get_current_business()
    
    if request.method == "POST":
        form = VariantAttributeValueForm(request.POST, business=current_business)
        if form.is_valid():
            if current_business:
                try:
                    # Save the attribute value with business context
                    attribute_value = form.save(commit=False)
                    attribute_value.business = current_business
                    attribute_value.save()
                    messages.success(request, "Variant attribute value created successfully!")
                    return redirect("products:variant_attribute_value_list")
                except IntegrityError as e:
                    messages.error(
                        request,
                        f"An error occurred while creating the variant attribute value: {str(e)}",
                    )
            else:
                messages.error(
                    request,
                    "No business context found. Please select a business before creating variant attribute values.",
                )
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = VariantAttributeValueForm(business=current_business)
    
    context = {
        "form": form,
        "title": "Create Variant Attribute Value",
    }
    
    return render(request, "products/variant_attribute_values/form.html", context)


@login_required
def variant_attribute_value_update(request, pk):
    """Update a specific variant attribute value"""
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_edit"
    ):
        messages.error(request, "You do not have permission to edit variant attribute values.")
        return redirect("products:list")
    
    attribute_value = get_object_or_404(VariantAttributeValue.objects.business_specific(), pk=pk)
    
    # Get the current business from the request
    from superadmin.middleware import get_current_business
    current_business = get_current_business()
    
    if request.method == "POST":
        form = VariantAttributeValueForm(request.POST, instance=attribute_value, business=current_business)
        if form.is_valid():
            if current_business:
                # Save the attribute value with business context
                attribute_value = form.save(commit=False)
                attribute_value.business = current_business
                attribute_value.save()
                messages.success(request, "Variant attribute value updated successfully!")
                return redirect("products:variant_attribute_value_list")
            else:
                messages.error(
                    request,
                    "No business context found. Please select a business before updating variant attribute values.",
                )
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = VariantAttributeValueForm(instance=attribute_value, business=current_business)
    
    context = {
        "form": form,
        "attribute_value": attribute_value,
        "title": "Update Variant Attribute Value",
    }
    
    return render(request, "products/variant_attribute_values/form.html", context)


@login_required
def variant_attribute_value_delete(request, pk):
    """Delete a specific variant attribute value"""
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_delete"
    ):
        messages.error(request, "You do not have permission to delete variant attribute values.")
        return redirect("products:list")
    
    attribute_value = get_object_or_404(VariantAttributeValue.objects.business_specific(), pk=pk)
    
    if request.method == "POST":
        attribute_value.is_active = False
        attribute_value.save()
        messages.success(request, "Variant attribute value deleted successfully!")
        return redirect("products:variant_attribute_value_list")
    
    context = {
        "attribute_value": attribute_value,
    }
    
    return render(request, "products/variant_attribute_values/confirm_delete.html", context)
