from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models.manager import Manager
    from customers.models import Customer as CustomerModel
    from products.models import Product as ProductModel
    from .models import Sale as SaleModel, Refund as RefundModel

from .models import Sale, SaleItem, Refund
from .forms import SaleForm
from products.models import Product
from customers.models import Customer
from superadmin.models import Business
from superadmin.middleware import get_current_business
from authentication.utils import check_user_permission
import json

@login_required
def sale_list(request):
    sales = Sale.objects.business_specific().all().prefetch_related('items__product')
    return render(request, 'sales/list.html', {'sales': sales})

@login_required
def sale_create(request):
    # Account owners have access to everything
    if request.user.role != 'admin' and not check_user_permission(request.user, 'can_create'):
        messages.error(request, 'You do not have permission to create sales.')
        return redirect('sales:list')
        
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            # Get current business from session
            current_business = None
            if 'current_business_id' in request.session:
                try:
                    current_business = Business.objects.get(id=request.session['current_business_id'])
                except Business.DoesNotExist:
                    pass
            
            if not current_business:
                messages.error(request, 'No business context found.')
                return redirect('sales:list')
            
            # Save the sale with business context
            sale = form.save(commit=False)
            sale.business = current_business
            sale.save()
            messages.success(request, 'Sale created successfully!')
            return redirect('sales:detail', pk=sale.pk)
    else:
        form = SaleForm()
    
    return render(request, 'sales/form.html', {'form': form, 'title': 'Create Sale'})

@login_required
def sale_update(request, pk):
    # Account owners have access to everything
    if request.user.role != 'admin' and not check_user_permission(request.user, 'can_edit'):
        messages.error(request, 'You do not have permission to edit sales.')
        return redirect('sales:list')
        
    sale = get_object_or_404(Sale.objects.business_specific(), pk=pk)
    
    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sale updated successfully!')
            return redirect('sales:detail', pk=sale.pk)
    else:
        form = SaleForm(instance=sale)
    
    return render(request, 'sales/form.html', {
        'form': form, 
        'title': 'Update Sale',
        'sale': sale
    })

@login_required
def sale_delete(request, pk):
    # Account owners have access to everything
    if request.user.role != 'admin' and not check_user_permission(request.user, 'can_delete'):
        messages.error(request, 'You do not have permission to delete sales.')
        return redirect('sales:list')
        
    sale = get_object_or_404(Sale.objects.business_specific(), pk=pk)
    
    if request.method == 'POST':
        # Before deleting, we need to restore the product quantities
        # This requires reversing the sale items
        with transaction.atomic():  # type: ignore
            # Restore product quantities
            for item in sale.items.all():
                product = item.product
                product.quantity = F('quantity') + item.quantity
                product.save()
            
            # Delete the sale (this will cascade delete sale items due to foreign key)
            sale.delete()
            
            messages.success(request, 'Sale deleted successfully!')
            return redirect('sales:list')
    
    return render(request, 'sales/confirm_delete.html', {'sale': sale})

@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale.objects.business_specific(), pk=pk)
    return render(request, 'sales/detail.html', {'sale': sale})

@login_required
def sale_refund(request, pk):
    sale = get_object_or_404(Sale.objects.business_specific(), pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        refund_amount = request.POST.get('refund_amount')
        
        if reason and refund_amount:
            try:
                refund_amount = float(refund_amount)
                if refund_amount > float(sale.total_amount):
                    messages.error(request, 'Refund amount cannot exceed sale total.')
                else:
                    # Process refund (in a real app, you would integrate with payment providers)
                    refund = Refund.objects.create(  # type: ignore
                        sale=sale,
                        reason=reason,
                        refund_amount=refund_amount
                    )
                    sale.is_refunded = True
                    sale.save()
                    messages.success(request, 'Refund processed successfully!')
                    return redirect('sales:detail', pk=sale.pk)
            except ValueError:
                messages.error(request, 'Invalid refund amount.')
        else:
            messages.error(request, 'Please provide a reason and refund amount.')
    
    return render(request, 'sales/refund.html', {'sale': sale})

@login_required
def pos_view(request):
    from settings.models import BusinessSettings
    try:
        business_settings = BusinessSettings.objects.get(id=1)
    except BusinessSettings.DoesNotExist:
        business_settings = BusinessSettings.objects.create(
            id=1,
            business_name='Smart Solution',
            business_address='123 Business Street, City, Country',
            business_email='info@smartsolution.com',
            business_phone='+1 (555) 123-4567',
            currency='USD',
            currency_symbol='$',
            tax_rate=0
        )
    
    # Ensure business context is properly set
    current_business = None
    
    # Try to get business from session first
    if 'current_business_id' in request.session:
        try:
            current_business = Business.objects.get(id=request.session['current_business_id'])
        except Business.DoesNotExist:
            # If business doesn't exist, remove from session
            if 'current_business_id' in request.session:
                del request.session['current_business_id']
    
    # If no business in session, try to get from middleware
    if not current_business:
        current_business = get_current_business()
    
    # If still no business, try to get the first business owned by user
    if not current_business and request.user.is_authenticated:
        user_businesses = Business.objects.filter(owner=request.user)
        if user_businesses.exists():
            current_business = user_businesses.first()
            # Set it in session for consistency
            request.session['current_business_id'] = current_business.id
    
    # If we have a business, ensure it's set in both session and middleware
    if current_business:
        request.session['current_business_id'] = current_business.id
        from superadmin.middleware import set_current_business
        set_current_business(current_business)
    
    # Get products and customers for the current business
    products = Product.objects.business_specific().filter(is_active=True)
    customers = Customer.objects.business_specific().filter(is_active=True)
    
    return render(request, 'sales/pos_modern.html', {
        'products': products,
        'customers': customers,
        'business_settings': business_settings
    })

@login_required
def test_scanner_view(request):
    return render(request, 'sales/test_scanner.html')

@login_required
def pos_scanner_test_view(request):
    return render(request, 'sales/pos_scanner_test.html')

@login_required
def camera_test_view(request):
    return render(request, 'sales/camera_test.html')

@login_required
def automatic_scanner_test_view(request):
    return render(request, 'sales/automatic_scanner_test.html')

@login_required
def simple_camera_test_view(request):
    return render(request, 'sales/simple_camera_test.html')

@login_required
def scanner_diagnostics_view(request):
    return render(request, 'sales/scanner_diagnostics.html')

@login_required
def scanner_debug_view(request):
    return render(request, 'sales/scanner_debug.html')

@login_required
@require_http_methods(["POST"])
def process_pos_sale(request):
    """Process a POS sale from the frontend"""
    try:
        # Log the request for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"=== STARTING POS SALE PROCESSING ===")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request user: {request.user}")
        logger.info(f"Session data: {dict(request.session)}")
        logger.info(f"Request body: {request.body}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Check if user has a business context
        current_business = None
        
        # Try to get business from session first
        if 'current_business_id' in request.session:
            try:
                current_business = Business.objects.get(id=request.session['current_business_id'])
                logger.info(f"Current business from session: {current_business}")
            except Business.DoesNotExist:
                logger.error("Business not found for ID in session")
                # Remove invalid business ID from session
                if 'current_business_id' in request.session:
                    del request.session['current_business_id']
        else:
            logger.warning("No current_business_id in session")
        
        # If we don't have business from session, try to get it from middleware
        if not current_business:
            try:
                from superadmin.middleware import get_current_business
                current_business = get_current_business()
                if current_business:
                    logger.info(f"Current business from middleware: {current_business}")
                    # Also set it in session for consistency
                    request.session['current_business_id'] = current_business.id
                else:
                    logger.error("No current business found from middleware")
            except Exception as e:
                logger.error(f"Error getting business from middleware: {str(e)}")
        
        # If still no business, try to get the first business owned by the user
        if not current_business:
            try:
                user_businesses = Business.objects.filter(owner=request.user)
                if user_businesses.exists():
                    current_business = user_businesses.first()
                    logger.info(f"Current business from user ownership: {current_business}")
                    # Set it in session for future requests
                    request.session['current_business_id'] = current_business.id
                else:
                    logger.error("No business found for user")
            except Exception as e:
                logger.error(f"Error getting user businesses: {str(e)}")
        
        if not current_business:
            logger.error("No business context found for user")
            return JsonResponse({
                'error': 'Business context not found. Please select a business before processing sales.'
            }, status=400)
        
        # Parse the JSON data from the request
        import json
        try:
            data = json.loads(request.body)
            logger.info(f"Request data parsed successfully: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON data: {str(e)}")
            logger.error(f"Raw request body: {request.body}")
            return JsonResponse({
                'error': 'Invalid request data format. Please try again.'
            }, status=400)
        
        # Extract sale data
        customer_id = data.get('customer_id')
        payment_method = data.get('payment_method', 'cash')
        discount = float(data.get('discount', 0))
        cart_items = data.get('cart_items', [])
        
        logger.info(f"Sale data extracted - Customer ID: {customer_id}, Payment method: {payment_method}, Discount: {discount}, Cart items: {len(cart_items)}")
        
        if not cart_items:
            logger.warning("No items in cart")
            return JsonResponse({
                'error': 'Cannot process sale: Your cart is empty. Please add items to the cart before checkout.'
            }, status=400)
        
        # Validate cart items
        for i, item in enumerate(cart_items):
            logger.info(f"Validating cart item {i}: {item}")
            if 'id' not in item or 'price' not in item or 'quantity' not in item:
                logger.error(f"Invalid cart item format: {item}")
                return JsonResponse({
                    'error': 'Invalid cart data. Please refresh the page and try again.'
                }, status=400)
        
        # Calculate totals
        subtotal = 0
        for item in cart_items:
            try:
                price = float(item['price'])
                quantity = float(item['quantity'])
                item_total = price * quantity
                subtotal += item_total
                logger.info(f"Item calculation - Price: {price}, Quantity: {quantity}, Total: {item_total}, Running subtotal: {subtotal}")
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid price or quantity in cart item: {item}")
                return JsonResponse({
                    'error': f'Invalid price or quantity for item: {item.get("name", "Unknown")}'
                }, status=400)
        
        tax = 0  # For now, no tax
        total_amount = subtotal + tax - discount
        
        logger.info(f"Calculated totals - Subtotal: {subtotal}, Tax: {tax}, Discount: {discount}, Total: {total_amount}")
        
        # Validate totals
        if total_amount < 0:
            logger.error("Total amount is negative")
            return JsonResponse({
                'error': 'Invalid discount amount. Discount cannot exceed the subtotal.'
            }, status=400)
        
        # Create the sale in a transaction
        logger.info("Starting database transaction")
        with transaction.atomic():  # type: ignore
            # Create the sale
            sale_data = {
                'subtotal': subtotal,
                'tax': tax,
                'discount': discount,
                'total_amount': total_amount,
                'payment_method': payment_method,
                'business': current_business,  # Associate with current business
            }
            
            logger.info(f"Preparing sale data: {sale_data}")
            
            if customer_id:
                # Verify customer belongs to current business
                try:
                    customer = Customer.objects.business_specific().get(pk=customer_id)
                    sale_data['customer'] = customer
                    logger.info(f"Customer found: {customer}")
                except Customer.DoesNotExist:
                    logger.warning(f"Customer {customer_id} not found in current business")
                    # Continue without customer
            
            logger.info(f"Creating sale with data: {sale_data}")
            try:
                sale = Sale.objects.create(**sale_data)  # type: ignore
                logger.info(f"Sale created with ID: {sale.pk}")
            except Exception as e:
                logger.error(f"Error creating sale: {str(e)}")
                return JsonResponse({
                    'error': f'Error creating sale record: {str(e)}'
                }, status=500)
            
            # Create sale items (stock will be automatically updated by signals)
            for i, item in enumerate(cart_items):
                product_id = item['id']
                quantity = float(item['quantity'])
                price = float(item['price'])
                total_price = quantity * price
                
                logger.info(f"Creating sale item {i} - Product ID: {product_id}, Quantity: {quantity}, Price: {price}")
                
                # Verify product belongs to current business
                try:
                    product = Product.objects.business_specific().get(pk=product_id)
                    logger.info(f"Product found: {product}")
                except Product.DoesNotExist:
                    logger.error(f"Product {product_id} not found in current business")
                    return JsonResponse({
                        'error': f'Product not found: {item.get("name", "Unknown product")}. Please refresh and try again.'
                    }, status=400)
                
                # Check if sufficient stock is available
                if float(product.quantity) < quantity:
                    logger.error(f"Insufficient stock for product {product.name}")
                    return JsonResponse({
                        'error': f'Insufficient stock for {product.name}. Available: {product.quantity}, Requested: {quantity}'
                    }, status=400)
                
                # Create sale item
                try:
                    sale_item = SaleItem.objects.create(  # type: ignore
                        sale=sale,
                        product=product,  # Use the product object instead of product_id
                        quantity=quantity,
                        unit_price=price,
                        total_price=total_price,
                        business=current_business  # Set business context for multi-tenancy
                    )
                    logger.info(f"Sale item created: {sale_item}")
                except Exception as e:
                    logger.error(f"Error creating sale item: {str(e)}")
                    return JsonResponse({
                        'error': f'Error creating sale item: {str(e)}'
                    }, status=500)
                
                # Note: Product quantity is now automatically updated by signals
                # No need to manually update product.quantity here
            
        logger.info(f"=== SALE PROCESSED SUCCESSFULLY! Sale ID: {sale.pk} ===")
        return JsonResponse({
            'success': True,
            'sale_id': sale.pk,
            'message': 'Sale processed successfully!'
        })
        
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"=== UNEXPECTED ERROR IN POS SALE PROCESSING ===")
        logger.error(f"Error processing POS sale: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("=== END ERROR DETAILS ===")
        return JsonResponse({
            'error': f'An unexpected error occurred while processing your sale. Please try again. Error details: {str(e)}'
        }, status=500)

def get_product_details(request, product_id):
    """AJAX view to get product details for POS - No login required for product details"""
    try:
        product = get_object_or_404(Product.objects.business_specific(), pk=product_id)
        data = {
            'id': product.pk,
            'name': product.name,
            'price': float(product.selling_price),
            'stock': float(product.quantity),
            'unit': product.unit.symbol
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_product_by_barcode(request, barcode):
    """AJAX view to get product details by barcode"""
    try:
        product = get_object_or_404(Product.objects.business_specific(), barcode=barcode)
        data = {
            'id': product.pk,
            'name': product.name,
            'price': float(product.selling_price),
            'stock': float(product.quantity),
            'unit': product.unit.symbol
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)