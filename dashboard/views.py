from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from products.models import Product, Category
from sales.models import Sale, SaleItem
from customers.models import Customer
from purchases.models import PurchaseOrder
from expenses.models import Expense
from suppliers.models import Supplier  # Add this import
from django.db.models import Sum, Count, F
from decimal import Decimal
from superadmin.models import Business
from superadmin.middleware import set_current_business  # Import the middleware function
from django.utils import timezone
import logging
import json
from datetime import date, datetime

# Add this import for search functionality
from django.db.models import Q

# Set up logging
logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    logger.info("=== DASHBOARD VIEW START ===")
    logger.info(f"User: {request.user}")
    logger.info(f"Session: {dict(request.session)}")

    # Check if there's a current business in the session
    current_business = None
    if "current_business_id" in request.session:
        try:
            current_business = Business.objects.get(
                id=request.session["current_business_id"]
            )
            logger.info(f"Found business in session: {current_business}")
        except Business.DoesNotExist:
            # If the business doesn't exist, remove it from session
            logger.warning("Business not found in session, removing from session")
            del request.session["current_business_id"]
            current_business = None
    else:
        logger.warning("No current_business_id in session")

    # If no business is selected, try to get the first business owned by the user
    if not current_business:
        user_businesses = Business.objects.filter(owner=request.user)
        logger.info(f"User businesses count: {user_businesses.count()}")
        if user_businesses.exists():
            current_business = user_businesses.first()
            logger.info(f"Using first business: {current_business}")
            # Set it in the session for future requests
            request.session["current_business_id"] = current_business.id
        else:
            logger.warning(
                "No businesses found for user, redirecting to create business"
            )
            # Check if user has just registered and needs to create a business
            # Redirect to business creation page
            return redirect("authentication:create_business")

    # IMPORTANT: Set the current business in middleware thread-local storage
    # This is required for business_specific() manager method to work properly
    if current_business:
        set_current_business(current_business)
        logger.info(f"Set current business in middleware: {current_business}")

    # Get business-specific data using business_specific() manager
    logger.info(f"Fetching business-specific data for business: {current_business}")
    products = Product.objects.business_specific()
    categories = Category.objects.business_specific()
    sales = Sale.objects.business_specific()
    customers = Customer.objects.business_specific()
    purchases = PurchaseOrder.objects.business_specific()
    expenses = Expense.objects.business_specific()

    logger.info(f"Products count: {products.count()}")
    logger.info(f"Categories count: {categories.count()}")
    logger.info(f"Sales count: {sales.count()}")
    logger.info(f"Customers count: {customers.count()}")
    logger.info(f"Purchases count: {purchases.count()}")
    logger.info(f"Expenses count: {expenses.count()}")

    # Calculate dashboard statistics
    total_products = products.count()
    total_categories = categories.count()
    total_sales = sales.count()
    total_customers = customers.count()
    total_purchases = purchases.count()

    # Calculate today's sales
    today = timezone.now().date()
    today_sales_queryset = sales.filter(sale_date__date=today)
    today_sales = today_sales_queryset.count()
    logger.info(f"Today's sales count: {today_sales}")

    # Calculate low stock products
    low_stock_products = products.filter(quantity__lte=F("reorder_level"))
    low_stock_count = low_stock_products.count()
    logger.info(f"Low stock products count: {low_stock_count}")

    # Calculate out of stock products
    out_of_stock_count = products.filter(quantity=0).count()
    logger.info(f"Out of stock products count: {out_of_stock_count}")

    # Calculate product value in stock (total worth)
    product_value_in_stock = Decimal("0.00")
    for product in products:
        product_value = product.selling_price * product.quantity
        product_value_in_stock += product_value

    logger.info(f"Product value in stock: {product_value_in_stock}")

    # Calculate today's profit
    today_profit = Decimal("0.00")
    today_sales_objects = today_sales_queryset
    for sale in today_sales_objects:
        today_profit += sale.total_profit
        logger.info(f"Sale {sale.id} profit: {sale.total_profit}")

    logger.info(f"Today's total profit: {today_profit}")

    # Calculate total profit (profit from all sales)
    total_profit = Decimal("0.00")
    all_sales = sales.all()
    for sale in all_sales:
        total_profit += sale.total_profit

    logger.info(f"Total profit: {total_profit}")

    # Prepare data for Fast-Moving vs Slow-Moving Items chart
    # Get top 5 and bottom 5 products by quantity sold
    product_sales_data = (
        SaleItem.objects.business_specific()
        .values("product__name")
        .annotate(total_quantity=Sum("quantity"), total_revenue=Sum("total_price"))
        .order_by("-total_quantity")
    )

    # Convert to list to allow indexing
    product_sales_list = list(product_sales_data)

    # Ensure we have data for both fast and slow moving products
    if len(product_sales_list) >= 10:
        fast_moving_products = product_sales_list[:5]  # Top 5
        slow_moving_products = product_sales_list[-5:]  # Bottom 5
    elif len(product_sales_list) >= 2:
        # Split the data in half if we have at least 2 items
        mid_point = len(product_sales_list) // 2
        fast_moving_products = product_sales_list[:mid_point]
        slow_moving_products = product_sales_list[mid_point:]
    else:
        # If we have 0 or 1 items, put them in fast moving
        fast_moving_products = product_sales_list
        slow_moving_products = []

    # Prepare data for Category-wise Stock Distribution chart
    category_stock_data = (
        products.values("category__name")
        .annotate(
            total_quantity=Sum("quantity"),
            total_value=Sum(F("selling_price") * F("quantity")),
        )
        .order_by("-total_value")
    )

    # Prepare data for Daily Sales Chart (last 7 days)
    # Get sales for the last 7 days
    seven_days_ago = today - timezone.timedelta(days=7)
    daily_sales_data = (
        sales.filter(sale_date__date__gte=seven_days_ago, sale_date__date__lte=today)
        .extra({"date": "date(sale_date)"})
        .values("date")
        .annotate(total_sales=Sum("total_amount"), count=Count("id"))
        .order_by("date")
    )

    # Prepare data for Top Selling Products chart
    top_selling_products = product_sales_list[:10] if product_sales_list else []

    # Convert Decimal and date values to JSON serializable formats
    def convert_to_serializable(data):
        if isinstance(data, list):
            return [convert_to_serializable(item) for item in data]
        elif isinstance(data, dict):
            return {key: convert_to_serializable(value) for key, value in data.items()}
        elif isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, (date, datetime)):
            return data.isoformat()
        else:
            return data

    # Ensure we have proper data structures for all chart data
    # Convert QuerySets to lists and handle empty data cases
    fast_moving_products = list(fast_moving_products) if fast_moving_products else []
    slow_moving_products = list(slow_moving_products) if slow_moving_products else []
    category_stock_data = list(category_stock_data) if category_stock_data else []
    daily_sales_data = list(daily_sales_data) if daily_sales_data else []
    top_selling_products = list(top_selling_products) if top_selling_products else []

    # Log the raw data for debugging
    logger.info(f"Fast moving products: {fast_moving_products}")
    logger.info(f"Slow moving products: {slow_moving_products}")
    logger.info(f"Category stock data: {category_stock_data}")
    logger.info(f"Daily sales data: {daily_sales_data}")
    logger.info(f"Top selling products: {top_selling_products}")

    # Convert all chart data to ensure proper JSON serialization
    fast_moving_products = convert_to_serializable(fast_moving_products)
    slow_moving_products = convert_to_serializable(slow_moving_products)
    category_stock_data = convert_to_serializable(category_stock_data)
    daily_sales_data = convert_to_serializable(daily_sales_data)
    top_selling_products = convert_to_serializable(top_selling_products)

    # Ensure we always have the expected structure for fast/slow data
    fast_slow_products_data = {
        "fast_moving": fast_moving_products if fast_moving_products else [],
        "slow_moving": slow_moving_products if slow_moving_products else [],
    }

    # Convert data to JSON for JavaScript
    fast_slow_products_json = json.dumps(fast_slow_products_data)

    category_stock_json = json.dumps(category_stock_data)
    daily_sales_json = json.dumps(daily_sales_data)
    top_selling_json = json.dumps(top_selling_products)

    context = {
        "total_products": total_products,
        "total_categories": total_categories,
        "total_sales": total_sales,
        "total_customers": total_customers,
        "total_purchases": total_purchases,
        "todays_sales_count": today_sales,  # Changed to match template variable name
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "product_value_in_stock": product_value_in_stock,
        "today_profit": today_profit,
        "total_profit": total_profit,
        "low_stock_products": low_stock_products[:5],  # Limit to 5 for display
        "current_business": current_business,
        # Chart data
        "fast_slow_products_json": fast_slow_products_json,
        "category_stock_json": category_stock_json,
        "daily_sales_json": daily_sales_json,
        "top_selling_json": top_selling_json,
    }

    logger.info(f"Context data: {context}")
    logger.info("=== DASHBOARD VIEW END ===")

    return render(request, "dashboard.html", context)


@login_required
def search_view(request):
    """
    Global search view that searches across products, sales, customers, etc.
    """
    query = request.GET.get("q", "")

    if not query:
        return render(
            request, "dashboard/search_results.html", {"query": query, "results": {}}
        )

    # Get current business from middleware
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    if not current_business:
        return render(
            request,
            "dashboard/search_results.html",
            {"query": query, "results": {}, "error": "No business context found"},
        )

    # Search products
    products = Product.objects.business_specific().filter(
        Q(name__icontains=query)
        | Q(sku__icontains=query)
        | Q(description__icontains=query)
        | Q(category__name__icontains=query)
    )

    # Search sales
    sales = Sale.objects.business_specific().filter(
        Q(customer__full_name__icontains=query) | Q(id__icontains=query)
    )

    # Search customers
    customers = Customer.objects.business_specific().filter(
        Q(full_name__icontains=query)
        | Q(email__icontains=query)
        | Q(phone__icontains=query)
    )

    # Search suppliers
    suppliers = Supplier.objects.business_specific().filter(
        Q(name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query)
    )

    # Search categories
    categories = Category.objects.business_specific().filter(Q(name__icontains=query))

    context = {
        "query": query,
        "results": {
            "products": products[:10],  # Limit to 10 results
            "sales": sales[:10],
            "customers": customers[:10],
            "suppliers": suppliers[:10],
            "categories": categories[:10],
        },
    }

    return render(request, "dashboard/search_results.html", context)
