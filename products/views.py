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
import qrcode
import csv
import io
from decimal import Decimal
from .models import Product, Category, Unit
from .forms import ProductForm, CategoryForm, UnitForm
from .utils import generate_product_qr_code

@login_required
def product_list(request):
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')
    
    # Start with all active products, filtered by business context
    products = Product.objects.business_specific().filter(is_active=True).select_related('category', 'unit')
    
    # Apply search filter
    if search_query:
        # Build a single Q object with all search conditions to avoid type checking issues
        search_filter = (
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(description__icontains=search_query)
        )
        products = products.filter(search_filter)
    
    # Apply category filter
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Apply status filter
    if status:
        if status == 'low_stock':
            products = products.filter(quantity__lte=F('reorder_level'))
        elif status == 'active':
            products = products.filter(is_active=True)
        elif status == 'inactive':
            products = products.filter(is_active=False)
    
    # Get categories for filter dropdown, filtered by business context
    categories = Category.objects.business_specific().all()
    
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_status': status,
    }
    
    return render(request, 'products/list.html', context)

@login_required
@require_http_methods(["GET"])
def product_search_ajax(request):
    """
    AJAX view for real-time product search
    Returns JSON response with matching products
    """
    search_query = request.GET.get('q', '')
    
    if len(search_query) < 1:
        return JsonResponse({'products': []})
    
    # Build a single Q object with all search conditions to avoid type checking issues
    search_filter = (
        Q(name__icontains=search_query) |
        Q(sku__icontains=search_query) |
        Q(description__icontains=search_query)
    )
    
    # Search for products matching the query, filtered by business context
    products = Product.objects.business_specific().filter(search_filter).filter(is_active=True)[:10]  # Limit to 10 results for performance
    
    # Format products for JSON response
    product_list = []
    for product in products:
        product_list.append({
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'selling_price': float(product.selling_price),
            'quantity': float(product.quantity),
            'unit': product.unit.symbol if product.unit else '',
            'category': product.category.name if product.category else '',
        })
    
    return JsonResponse({'products': product_list})

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
        return JsonResponse({'error': 'No business context found'}, status=400)
    
    try:
        # Make sure the product belongs to the current business
        product = get_object_or_404(Product.objects.filter(business=current_business), pk=pk, is_active=True)
        return JsonResponse({
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'cost_price': float(product.cost_price),
            'selling_price': float(product.selling_price),
            'quantity': float(product.quantity),
            'unit': product.unit.symbol if product.unit else '',
            'category': product.category.name if product.category else '',
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

@login_required
def product_create(request):
    # Get the current business from the request
    from superadmin.middleware import get_current_business
    current_business = get_current_business()
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, business=current_business)
        if form.is_valid():
            if current_business:
                try:
                    # Save the product with business context
                    product = form.save(commit=False)
                    product.business = current_business
                    product.save()
                    messages.success(request, 'Product created successfully!')
                    return redirect('products:list')
                except IntegrityError as e:
                    if 'products_product_business_id_sku_cee6e09f_uniq' in str(e):
                        messages.error(request, 'A product with this SKU already exists for your business. Please use a different SKU.')
                    else:
                        messages.error(request, f'An error occurred while creating the product: {str(e)}')
            else:
                messages.error(request, 'No business context found. Please select a business before creating products.')
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
    else:
        form = ProductForm(business=current_business)
    
    return render(request, 'products/form.html', {'form': form, 'title': 'Create Product'})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.business_specific(), pk=pk)
    
    # Generate QR code for the product
    qr_buffer = generate_product_qr_code(product)
    
    context = {
        'product': product,
        'qr_code_data': qr_buffer.getvalue() if qr_buffer else None,
        'MEDIA_URL': settings.MEDIA_URL
    }
    
    return render(request, 'products/detail.html', context)

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product.objects.business_specific(), pk=pk)
    
    # Get the current business from the request
    from superadmin.middleware import get_current_business
    current_business = get_current_business()
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product, business=current_business)
        if form.is_valid():
            if current_business:
                # Save the product with business context
                product = form.save(commit=False)
                product.business = current_business
                product.save()
                messages.success(request, 'Product updated successfully!')
                return redirect('products:detail', pk=product.pk)
            else:
                messages.error(request, 'No business context found. Please select a business before updating products.')
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
    else:
        form = ProductForm(instance=product, business=current_business)
    
    return render(request, 'products/form.html', {
        'form': form, 
        'title': 'Update Product',
        'product': product
    })

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product.objects.business_specific(), pk=pk)
    
    if request.method == 'POST':
        product.is_active = False
        product.save()
        messages.success(request, 'Product deleted successfully!')
        return redirect('products:list')
    
    return render(request, 'products/confirm_delete.html', {'product': product})

@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'products/categories/list.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
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
                messages.success(request, 'Category created successfully!')
                return redirect('products:category_list')
            else:
                messages.error(request, 'No business context found. Please select a business before creating categories.')
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
    else:
        form = CategoryForm()
    
    return render(request, 'products/categories/form.html', {'form': form, 'title': 'Create Category'})

@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
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
                messages.success(request, 'Category updated successfully!')
                return redirect('products:category_list')
            else:
                messages.error(request, 'No business context found. Please select a business before updating categories.')
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'products/categories/form.html', {
        'form': form, 
        'title': 'Update Category',
        'category': category
    })

@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('products:category_list')
    
    return render(request, 'products/categories/confirm_delete.html', {'category': category})

@login_required
def unit_list(request):
    units = Unit.objects.all()
    return render(request, 'products/units/list.html', {'units': units})

@login_required
def unit_create(request):
    if request.method == 'POST':
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
                messages.success(request, 'Unit created successfully!')
                return redirect('products:unit_list')
            else:
                messages.error(request, 'No business context found. Please select a business before creating units.')
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
    else:
        form = UnitForm()
    
    return render(request, 'products/units/form.html', {'form': form, 'title': 'Create Unit'})

@login_required
def bulk_upload(request):
    if request.method == 'POST':
        if 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            
            # Check if file is CSV
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a CSV file.')
                return redirect('products:bulk_upload')
            
            # Process the CSV file
            try:
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.reader(io_string, delimiter=',')
                
                # Skip header row
                next(reader)
                
                success_count = 0
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
                            
                        name, sku, barcode, category_name, unit_name, description, cost_price, selling_price, quantity, reorder_level, expiry_date = row
                        
                        # Validate required fields
                        if not name or not sku or not category_name or not unit_name:
                            errors.append(f"Row {i+2}: Missing required fields (name, sku, category, unit)")
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
                            defaults={'description': f'Category for {category_name}'}
                        )
                        
                        # Get or create unit
                        unit, _ = Unit.objects.get_or_create(
                            business=current_business,
                            name=unit_name,
                            defaults={'symbol': unit_name[:3].upper()}
                        )
                        
                        # Handle empty values
                        barcode = barcode if barcode else None
                        
                        # Create product
                        Product.objects.create(
                            business=current_business,
                            name=name,
                            sku=sku,
                            barcode=barcode,
                            category=category,
                            unit=unit,
                            description=description or '',
                            cost_price=Decimal(cost_price) if cost_price else Decimal('0'),
                            selling_price=Decimal(selling_price) if selling_price else Decimal('0'),
                            quantity=Decimal(quantity) if quantity else Decimal('0'),
                            reorder_level=Decimal(reorder_level) if reorder_level else Decimal('0'),
                            expiry_date=expiry_date if expiry_date else None
                        )
                        success_count += 1
                        
                    except Exception as e:
                        errors.append(f"Row {i+2}: {str(e)}")
                        error_count += 1
                
                if success_count > 0:
                    messages.success(request, f'Successfully imported {success_count} products.')
                if error_count > 0:
                    messages.error(request, f'Failed to import {error_count} products. Errors: {" ".join(errors)}')
                    
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')
                
        else:
            messages.error(request, 'No file uploaded.')
            
        return redirect('products:bulk_upload')
    
    return render(request, 'products/bulk_upload.html')

@login_required
def export_products_csv(request):
    # Create the HttpResponse object with the appropriate CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'
    
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'Name', 'SKU', 'Barcode', 'Category', 'Unit', 'Description',
        'Cost Price', 'Selling Price', 'Quantity', 'Reorder Level', 'Expiry Date'
    ])
    
    # Write data rows
    products = Product.objects.all().select_related('category', 'unit')
    for product in products:
        writer.writerow([
            product.name,
            product.sku,
            product.barcode or '',
            product.category.name,
            product.unit.name,
            product.description or '',
            product.cost_price,
            product.selling_price,
            product.quantity,
            product.reorder_level,
            product.expiry_date or ''
        ])
        
    return response

@login_required
def download_template(request):
    # Create the HttpResponse object with the appropriate CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products_template.csv"'
    
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'Name', 'SKU', 'Barcode', 'Category', 'Unit', 'Description',
        'Cost Price', 'Selling Price', 'Quantity', 'Reorder Level', 'Expiry Date'
    ])
    
    # Write sample data row
    writer.writerow([
        'Sample Product', 'SKU001', '123456789012', 'Electronics', 'Piece', 'Sample product description',
        '10.50', '15.99', '100', '10', '2025-12-31'
    ])
        
    return response