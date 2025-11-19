from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.contrib.sessions.models import Session
import json
import logging

from .models import Cart, CartItem, Sale, SaleItem
from products.models import Product
from customers.models import Customer
from superadmin.models import Business

logger = logging.getLogger(__name__)


def get_or_create_cart(request):
    """Get or create a cart for the current user/session"""
    try:
        logger.info("=== GET_OR_CREATE_CART START ===")

        # Try to get business context
        current_business = None
        if "current_business_id" in request.session:
            try:
                current_business = Business.objects.get(
                    id=request.session["current_business_id"]
                )
                logger.info(f"Found business in session: {current_business}")
            except Business.DoesNotExist:
                logger.warning("Business not found in session")
                pass
        else:
            logger.warning("No current_business_id in session")

        # If no business in session, try to get from middleware
        if not current_business:
            try:
                from superadmin.middleware import get_current_business

                current_business = get_current_business()
                if current_business:
                    logger.info(f"Found business from middleware: {current_business}")
                    # Also set it in session for consistency
                    request.session["current_business_id"] = current_business.id
                else:
                    logger.warning("No business found from middleware")
            except Exception as e:
                logger.error(f"Error getting business from middleware: {str(e)}")

        # If still no business, try to get the first business owned by the user
        if not current_business and request.user.is_authenticated:
            try:
                user_businesses = Business.objects.filter(owner=request.user)
                if user_businesses.exists():
                    current_business = user_businesses.first()
                    logger.info(
                        f"Found business from user ownership: {current_business}"
                    )
                    # Set it in session for future requests
                    request.session["current_business_id"] = current_business.id
                else:
                    logger.error("No business found for user")
            except Exception as e:
                logger.error(f"Error getting user businesses: {str(e)}")

        if not current_business:
            logger.error("No business context found for user")
            raise Exception(
                "Business context not found. Please select a business before processing sales."
            )

        # For logged-in users
        if request.user.is_authenticated:
            logger.info(f"User is authenticated: {request.user}")
            # Try to get the most recent cart for this user and business
            try:
                cart = (
                    Cart.objects.filter(user=request.user, business=current_business)
                    .order_by("-created_at")
                    .first()
                )

                if cart:
                    logger.info(
                        f"Found existing cart for authenticated user: {cart.id}"
                    )
                else:
                    # Create a new cart
                    session_key = request.session.session_key or ""
                    if not session_key:
                        request.session.create()
                        session_key = request.session.session_key
                    cart = Cart.objects.create(
                        user=request.user,
                        business=current_business,
                        session_key=session_key,
                    )
                    logger.info(f"Created new cart for authenticated user: {cart.id}")
            except Exception as e:
                logger.error(
                    f"Error getting/creating cart for authenticated user: {str(e)}"
                )
                raise
        else:
            # For anonymous users
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
                logger.info(f"Created new session with key: {session_key}")
            else:
                logger.info(f"Using existing session with key: {session_key}")

            # Try to get the most recent cart for this session and business
            try:
                cart = (
                    Cart.objects.filter(
                        session_key=session_key, business=current_business
                    )
                    .order_by("-created_at")
                    .first()
                )

                if cart:
                    logger.info(f"Found existing cart for anonymous user: {cart.id}")
                else:
                    # Create a new cart
                    cart = Cart.objects.create(
                        session_key=session_key, business=current_business, user=None
                    )
                    logger.info(f"Created new cart for anonymous user: {cart.id}")
            except Exception as e:
                logger.error(
                    f"Error getting/creating cart for anonymous user: {str(e)}"
                )
                raise

        logger.info(f"=== GET_OR_CREATE_CART END - Returning cart: {cart} ===")
        return cart
    except Exception as e:
        logger.error(f"Error in get_or_create_cart: {str(e)}")
        logger.exception("Full traceback for cart creation error:")
        raise


@require_http_methods(["POST"])
def add_to_cart(request):
    """Add a product to the cart"""
    try:
        logger.info("=== STARTING ADD_TO_CART PROCESS ===")

        # Log request details for debugging
        logger.info(f"Request user: {request.user}")
        logger.info(f"Request session: {dict(request.session)}")
        logger.info(f"Request body: {request.body}")

        # ADDITIONAL DEBUGGING: Check if user is authenticated
        if not request.user.is_authenticated:
            logger.error("User is not authenticated")
            return JsonResponse(
                {"error": "User is not authenticated. Please log in and try again."},
                status=401,
            )

        data = json.loads(request.body)
        product_id = data.get("product_id")
        quantity = data.get("quantity", 1)

        logger.info(f"Product ID: {product_id}, Quantity: {quantity}")

        if not product_id:
            logger.error("Product ID is required")
            return JsonResponse({"error": "Product ID is required"}, status=400)

        # Get the product
        try:
            product = get_object_or_404(
                Product.objects.business_specific(), pk=product_id
            )
            logger.info(f"Found product: {product}")
        except Exception as e:
            logger.error(f"Error finding product: {str(e)}")
            return JsonResponse({"error": f"Product not found: {str(e)}"}, status=404)

        # Check stock
        try:
            product_quantity = float(product.quantity)
            requested_quantity = float(quantity)
            if product_quantity < requested_quantity:
                logger.error(
                    f"Insufficient stock. Available: {product_quantity}, Requested: {requested_quantity}"
                )
                return JsonResponse(
                    {
                        "error": f"Insufficient stock. Only {product.quantity} items available."
                    },
                    status=400,
                )
        except Exception as e:
            logger.error(f"Error checking stock: {str(e)}")
            return JsonResponse(
                {"error": f"Error checking stock: {str(e)}"}, status=500
            )

        # Get or create cart
        try:
            cart = get_or_create_cart(request)
            logger.info(f"Cart: {cart}")
        except Exception as e:
            logger.error(f"Error getting or creating cart: {str(e)}")
            return JsonResponse(
                {"error": f"Error getting or creating cart: {str(e)}"}, status=500
            )

        # Add or update cart item
        try:
            # Note: CartItem doesn't have a business field, it gets business context from its cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={"quantity": quantity, "unit_price": product.selling_price},
            )

            if not created:
                # Update quantity if item already exists
                new_quantity = float(cart_item.quantity) + float(quantity)
                if float(product.quantity) < new_quantity:
                    logger.error(
                        f"Insufficient stock after update. Available: {product.quantity}, Requested: {new_quantity}"
                    )
                    return JsonResponse(
                        {
                            "error": f"Insufficient stock. Only {product.quantity} items available."
                        },
                        status=400,
                    )
                cart_item.quantity = new_quantity
                cart_item.save()
                logger.info(f"Updated existing cart item: {cart_item}")
            else:
                logger.info(f"Created new cart item: {cart_item}")

            # Prepare response data
            response_data = {
                "success": True,
                "message": f"{product.name} added to cart successfully!",
                "item": {
                    "id": cart_item.id,
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": float(cart_item.quantity),
                    "unit_price": float(cart_item.unit_price),
                    "total_price": float(cart_item.total_price),
                },
            }
            logger.info(f"Add to cart response: {response_data}")

            return JsonResponse(response_data)

        except Exception as e:
            logger.error(f"Error adding item to cart: {str(e)}")
            return JsonResponse(
                {"error": f"Error adding item to cart: {str(e)}"}, status=500
            )

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON data: {str(e)}")
        return JsonResponse(
            {"error": f"Invalid request data format: {str(e)}"}, status=400
        )
    except Exception as e:
        logger.error(f"Error in add_to_cart: {str(e)}")
        logger.exception("Full traceback for add to cart error:")
        return JsonResponse(
            {"error": f"An unexpected error occurred: {str(e)}"}, status=500
        )


@require_http_methods(["POST"])
def update_cart_item(request):
    """Update quantity of a cart item"""
    try:
        # ADDITIONAL DEBUGGING: Check if user is authenticated
        if not request.user.is_authenticated:
            logger.error("User is not authenticated")
            return JsonResponse(
                {"error": "User is not authenticated. Please log in and try again."},
                status=401,
            )

        data = json.loads(request.body)
        item_id = data.get("item_id")
        quantity = data.get("quantity")

        if not item_id or quantity is None:
            return JsonResponse(
                {"error": "Item ID and quantity are required"}, status=400
            )

        # Get cart item
        cart_item = get_object_or_404(CartItem.objects.business_specific(), pk=item_id)

        # Check stock
        if float(cart_item.product.quantity) < float(quantity):
            return JsonResponse(
                {
                    "error": f"Insufficient stock. Only {cart_item.product.quantity} items available."
                },
                status=400,
            )

        # Update quantity
        cart_item.quantity = quantity
        cart_item.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Cart item updated successfully",
                "cart_item": {
                    "id": cart_item.id,
                    "product_id": cart_item.product.id,
                    "product_name": cart_item.product.name,
                    "quantity": float(cart_item.quantity),
                    "unit_price": float(cart_item.unit_price),
                    "total_price": float(cart_item.total_price),
                },
            }
        )

    except Exception as e:
        logger.error(f"Error updating cart item: {str(e)}")
        return JsonResponse(
            {"error": f"Error updating cart item: {str(e)}"}, status=500
        )


@require_http_methods(["POST"])
def remove_from_cart(request):
    """Remove an item from the cart"""
    try:
        # ADDITIONAL DEBUGGING: Check if user is authenticated
        if not request.user.is_authenticated:
            logger.error("User is not authenticated")
            return JsonResponse(
                {"error": "User is not authenticated. Please log in and try again."},
                status=401,
            )

        data = json.loads(request.body)
        item_id = data.get("item_id")

        if not item_id:
            return JsonResponse({"error": "Item ID is required"}, status=400)

        # Get cart item
        cart_item = get_object_or_404(CartItem.objects.business_specific(), pk=item_id)

        # Delete the item
        cart_item.delete()

        return JsonResponse(
            {"success": True, "message": "Item removed from cart successfully"}
        )

    except Exception as e:
        logger.error(f"Error removing item from cart: {str(e)}")
        return JsonResponse(
            {"error": f"Error removing item from cart: {str(e)}"}, status=500
        )


def get_cart(request):
    """Get the current cart contents"""
    try:
        logger.info("=== GETTING CART CONTENTS ===")

        # ADDITIONAL DEBUGGING: Check if user is authenticated
        if not request.user.is_authenticated:
            logger.error("User is not authenticated")
            return JsonResponse(
                {"error": "User is not authenticated. Please log in and try again."},
                status=401,
            )

        logger.info(f"Request user: {request.user}")
        logger.info(f"Request session: {dict(request.session)}")

        cart = get_or_create_cart(request)
        logger.info(f"Cart retrieved: {cart}")

        cart_items = cart.items.select_related("product").all()
        logger.info(f"Cart items count: {cart_items.count()}")

        items_data = []
        for item in cart_items:
            item_data = {
                "id": item.id,
                "product_id": item.product.id,
                "product_name": item.product.name,
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price),
            }
            items_data.append(item_data)
            logger.info(f"Cart item: {item_data}")

        logger.info(f"Returning {len(items_data)} items")
        return JsonResponse({"success": True, "items": items_data})

    except Exception as e:
        logger.error(f"Error getting cart: {str(e)}")
        logger.exception("Full traceback for cart fetching error:")
        return JsonResponse({"error": f"Error getting cart: {str(e)}"}, status=500)


@require_http_methods(["POST"])
def clear_cart(request):
    """Clear all items from the cart"""
    try:
        # ADDITIONAL DEBUGGING: Check if user is authenticated
        if not request.user.is_authenticated:
            logger.error("User is not authenticated")
            return JsonResponse(
                {"error": "User is not authenticated. Please log in and try again."},
                status=401,
            )

        cart = get_or_create_cart(request)
        cart.items.all().delete()

        return JsonResponse({"success": True, "message": "Cart cleared successfully"})

    except Exception as e:
        logger.error(f"Error clearing cart: {str(e)}")
        return JsonResponse({"error": f"Error clearing cart: {str(e)}"}, status=500)


@require_http_methods(["POST"])
def process_sale_from_cart(request):
    """Process a sale from the cart"""
    try:
        logger.info("=== STARTING SALE PROCESSING ===")

        # Log request details for debugging
        logger.info(f"Request user: {request.user}")
        logger.info(f"Request session: {dict(request.session)}")
        logger.info(f"Request body: {request.body}")
        logger.info(f"Request headers: {dict(request.headers)}")

        # ADDITIONAL DEBUGGING: Check if user is authenticated
        if not request.user.is_authenticated:
            logger.error("User is not authenticated")
            return JsonResponse(
                {"error": "User is not authenticated. Please log in and try again."},
                status=401,
            )

        data = json.loads(request.body)
        customer_id = data.get("customer_id")
        payment_method = data.get("payment_method", "cash")
        discount = float(data.get("discount", 0))

        logger.info(
            f"Request data - Customer ID: {customer_id}, Payment method: {payment_method}, Discount: {discount}"
        )

        # Get current business with improved error handling
        current_business = None
        business_error = None

        # Try to get business from session first
        if "current_business_id" in request.session:
            try:
                current_business = Business.objects.get(
                    id=request.session["current_business_id"]
                )
                logger.info(f"Current business from session: {current_business}")
            except Business.DoesNotExist:
                business_error = "Business not found in session"
                logger.error(business_error)
            except Exception as e:
                business_error = f"Error getting business from session: {str(e)}"
                logger.error(business_error)
        else:
            business_error = "No current_business_id in session"
            logger.warning(business_error)

        # If we don't have business from session, try to get it from middleware
        if not current_business:
            try:
                from superadmin.middleware import get_current_business

                current_business = get_current_business()
                if current_business:
                    logger.info(f"Current business from middleware: {current_business}")
                    # Also set it in session for consistency
                    request.session["current_business_id"] = current_business.id
                else:
                    business_error = (
                        business_error or "No business found from middleware"
                    )
                    logger.error(business_error)
            except Exception as e:
                business_error = (
                    business_error
                    or f"Error getting business from middleware: {str(e)}"
                )
                logger.error(business_error)

        # If still no business, try to get the first business owned by the user
        if not current_business and request.user.is_authenticated:
            try:
                user_businesses = Business.objects.filter(owner=request.user)
                if user_businesses.exists():
                    current_business = user_businesses.first()
                    logger.info(
                        f"Current business from user ownership: {current_business}"
                    )
                    # Set it in session for future requests
                    request.session["current_business_id"] = current_business.id
                else:
                    business_error = business_error or "No business found for user"
                    logger.error(business_error)
            except Exception as e:
                business_error = (
                    business_error or f"Error getting user businesses: {str(e)}"
                )
                logger.error(business_error)

        if not current_business:
            error_message = (
                business_error
                or "Business context not found. Please select a business before processing sales."
            )
            logger.error(f"Final error: {error_message}")
            return JsonResponse({"error": error_message}, status=400)

        logger.info(f"Using business: {current_business}")

        # Get cart
        cart = get_or_create_cart(request)
        cart_items = cart.items.select_related("product").all()

        if not cart_items.exists():
            logger.warning("Cart is empty")
            return JsonResponse(
                {
                    "error": "Cannot process sale: Your cart is empty. Please add items to the cart before checkout."
                },
                status=400,
            )

        logger.info(f"Found {cart_items.count()} items in cart")

        # Calculate totals
        subtotal = 0
        for item in cart_items:
            subtotal += float(item.total_price)
            logger.info(
                f"Item: {item.product.name}, Quantity: {item.quantity}, Price: {item.unit_price}, Total: {item.total_price}"
            )

        tax = 0  # For now, no tax
        total_amount = subtotal + tax - discount

        logger.info(
            f"Calculated totals - Subtotal: {subtotal}, Tax: {tax}, Discount: {discount}, Total: {total_amount}"
        )

        if total_amount < 0:
            logger.error("Total amount is negative")
            return JsonResponse(
                {
                    "error": "Invalid discount amount. Discount cannot exceed the subtotal."
                },
                status=400,
            )

        # Create the sale in a transaction
        logger.info("Starting database transaction")
        with transaction.atomic():  # type: ignore
            # Create the sale
            sale_data = {
                "subtotal": subtotal,
                "tax": tax,
                "discount": discount,
                "total_amount": total_amount,
                "payment_method": payment_method,
                "business": current_business,
            }

            logger.info(f"Preparing sale data: {sale_data}")

            if customer_id:
                try:
                    customer = Customer.objects.business_specific().get(pk=customer_id)
                    sale_data["customer"] = customer
                    logger.info(f"Customer found: {customer}")
                except Customer.DoesNotExist:
                    logger.warning(
                        f"Customer {customer_id} not found in current business"
                    )
                    # Continue without customer

            logger.info(f"Creating sale with data: {sale_data}")
            try:
                sale = Sale.objects.create(**sale_data)
                logger.info(f"Sale created with ID: {sale.pk}")
            except Exception as e:
                logger.error(f"Error creating sale: {str(e)}")
                logger.exception("Full traceback for sale creation error:")
                return JsonResponse(
                    {"error": f"Error creating sale record: {str(e)}"}, status=500
                )

            # Create sale items
            logger.info("Creating sale items")
            for item in cart_items:
                # Check if sufficient stock is available
                if float(item.product.quantity) < float(item.quantity):
                    logger.error(f"Insufficient stock for {item.product.name}")
                    return JsonResponse(
                        {
                            "error": f"Insufficient stock for {item.product.name}. Available: {item.product.quantity}, Requested: {item.quantity}"
                        },
                        status=400,
                    )

                # Create sale item
                try:
                    sale_item = SaleItem.objects.create(
                        sale=sale,
                        product=item.product,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total_price=item.total_price,
                    )
                    logger.info(f"Sale item created: {sale_item}")
                except Exception as e:
                    logger.error(f"Error creating sale item: {str(e)}")
                    logger.exception("Full traceback for sale item creation error:")
                    return JsonResponse(
                        {"error": f"Error creating sale item: {str(e)}"}, status=500
                    )

            # Clear the cart after successful sale
            logger.info("Clearing cart")
            cart.items.all().delete()
            logger.info("Cart cleared successfully")

        logger.info("=== SALE PROCESSING COMPLETED SUCCESSFULLY ===")
        return JsonResponse(
            {
                "success": True,
                "sale_id": sale.pk,
                "message": "Sale processed successfully!",
            }
        )

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON data: {str(e)}")
        return JsonResponse(
            {"error": f"Invalid request data format: {str(e)}"}, status=400
        )
    except Exception as e:
        logger.error(f"Error processing sale: {str(e)}")
        logger.exception("Full traceback for sale processing error:")
        return JsonResponse(
            {
                "error": f"An unexpected error occurred while processing your sale. Please try again. Error details: {str(e)}"
            },
            status=500,
        )
