from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from products.models import Product, Category, StockAlert
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
from datetime import timedelta
import logging
import json
from datetime import date, datetime

# Add this import for search functionality
from django.db.models import Q

# Import AuditLog for recent activities
from settings.models import AuditLog

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
            logger.warning("Business not found in session")

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
                logger.info(f"Found business from user ownership: {current_business}")
                # Set it in session for future requests
                request.session["current_business_id"] = current_business.id
            else:
                logger.error("No businesses found for user")
        except Exception as e:
            logger.error(f"Error getting user businesses: {str(e)}")

    # If still no business, check if user has businesses associated with them
    if not current_business and request.user.is_authenticated:
        try:
            user_businesses = Business.objects.filter(
                Q(owner=request.user) | Q(managers=request.user) | Q(staff=request.user)
            ).distinct()
            if user_businesses.exists():
                current_business = user_businesses.first()
                logger.info(f"Found associated business: {current_business}")
                # Set it in session for future requests
                request.session["current_business_id"] = current_business.id
        except Exception as e:
            logger.error(f"Error getting associated businesses: {str(e)}")

    # If no business found at all, redirect to create business page
    if not current_business:
        try:
            # Check if user has any businesses
            user_businesses = Business.objects.filter(
                Q(owner=request.user) | Q(managers=request.user) | Q(staff=request.user)
            ).distinct()

            if not user_businesses.exists() and not request.user.is_superuser:
                logger.warning(
                    "No businesses found for user, redirecting to create business"
                )
                # Check if user has just registered and needs to create a business
                # Redirect to business creation page
                return redirect("authentication:create_business")
        except Exception as e:
            logger.error(f"Error checking user businesses: {str(e)}")

    # Check if the business is pending approval
    if current_business and current_business.status == "pending":
        # Show a message that the business is pending approval
        messages.info(
            request,
            "Your business registration is pending approval by an administrator. You will have full access once it's approved.",
        )
        # Render a special template for pending businesses
        return render(
            request, "dashboard/pending_business.html", {"business": current_business}
        )

    # IMPORTANT: Set the current business in middleware thread-local storage
    # This is required for business_specific() manager method to work properly
    if current_business:
        set_current_business(current_business)
        logger.info(f"Set current business in middleware: {current_business}")

    # Get business-specific data using business_specific() manager
    logger.info(f"Fetching business-specific data for business: {current_business}")

    if current_business:
        products = Product.objects.business_specific()
        categories = Category.objects.business_specific()
        sales = Sale.objects.business_specific()
        customers = Customer.objects.business_specific()
        purchases = PurchaseOrder.objects.business_specific()
        expenses = Expense.objects.business_specific()
        suppliers = Supplier.objects.business_specific()
    else:
        # Fallback to all data if no business context (for superusers in some cases)
        products = Product.objects.all()
        categories = Category.objects.all()
        sales = Sale.objects.all()
        customers = Customer.objects.all()
        purchases = PurchaseOrder.objects.all()
        expenses = Expense.objects.all()
        suppliers = Supplier.objects.all()

    # Calculate dashboard metrics
    total_products = products.count()
    total_categories = categories.count()
    total_sales = sales.count()
    total_customers = customers.count()
    total_purchases = purchases.count()

    # Today's sales
    today = timezone.now().date()
    today_sales = sales.filter(sale_date__date=today).count()

    # Today's sales amount
    today_sales_amount = sales.filter(sale_date__date=today).aggregate(
        total_amount=Sum("total_amount")
    )["total_amount"] or Decimal("0")

    # Low stock products
    low_stock_products = products.filter(quantity__lte=F("reorder_level"))
    low_stock_count = low_stock_products.count()

    # Out of stock products
    out_of_stock_count = products.filter(quantity=0).count()

    # Product value in stock
    product_value_in_stock = (
        products.aggregate(total_value=Sum(F("quantity") * F("cost_price")))[
            "total_value"
        ]
        or 0
    )

    # Profit calculations
    today_profit = Decimal("0")
    total_profit = Decimal("0")

    # Calculate today's profit
    today_sales_objects = sales.filter(sale_date__date=today).prefetch_related("items")
    for sale in today_sales_objects:
        for item in sale.items.all():
            # Use unit_price instead of selling_price
            profit_per_item = item.unit_price - item.product.cost_price
            today_profit += profit_per_item * item.quantity

    # Calculate total profit
    all_sales_objects = sales.prefetch_related("items")
    for sale in all_sales_objects:
        for item in sale.items.all():
            # Use unit_price instead of selling_price
            profit_per_item = item.unit_price - item.product.cost_price
            total_profit += profit_per_item * item.quantity

    # Calculate metrics for circular charts
    # Profit Margin = (Total Profit / Total Revenue) * 100
    total_revenue = Decimal("0")
    for sale in all_sales_objects:
        for item in sale.items.all():
            total_revenue += item.unit_price * item.quantity

    profit_margin = 0
    if total_revenue > 0:
        profit_margin = float((total_profit / total_revenue) * 100)

    # Inventory Turnover = Cost of Goods Sold / Average Inventory Value
    # For simplicity, we'll calculate it as number of sales / total products
    inventory_turnover = 0
    if total_products > 0:
        inventory_turnover = (
            float(total_sales) / float(total_products) * 10
        )  # Scale for display

    # Customer Retention Rate = Returning Customers / Total Customers * 100
    # For simplicity, we'll estimate based on sales frequency
    customer_retention = 0
    if total_customers > 0:
        # Estimate based on ratio of sales to customers
        customer_retention = min(
            float(total_sales) / float(total_customers) * 20, 100
        )  # Scale and cap at 100

    # Order Fulfillment Rate = Completed Orders / Total Orders * 100
    # For simplicity, we'll assume all sales are completed
    order_fulfillment = min(
        float(total_sales) / float(total_sales + 1) * 100, 95
    )  # Assume 95% for display

    # Chart data preparation
    # Fast vs Slow moving products (based on actual sales data)
    # Calculate product sales frequency over the last 30 days
    thirty_days_ago = today - timedelta(days=30)
    recent_sales = sales.filter(sale_date__gte=thirty_days_ago)

    # Get product sales counts
    product_sales_data = list(
        SaleItem.objects.filter(sale__in=recent_sales)
        .values("product__name")
        .annotate(total_sales=Count("product"), total_quantity=Sum("quantity"))
        .order_by("-total_sales")
    )

    # Separate fast and slow moving products
    fast_moving_products = (
        product_sales_data[:5] if len(product_sales_data) >= 5 else product_sales_data
    )
    slow_moving_products = (
        product_sales_data[-5:] if len(product_sales_data) >= 5 else product_sales_data
    )

    # Create labels from fast moving products (use slow moving if fast moving is empty)
    labels = (
        [item["product__name"] for item in fast_moving_products]
        if fast_moving_products
        else [item["product__name"] for item in slow_moving_products]
    )

    fast_slow_products_data = {
        "labels": labels[:5],
        "fast_moving": [item["total_sales"] for item in fast_moving_products[:5]],
        "slow_moving": (
            [item["total_sales"] for item in slow_moving_products[-5:]]
            if len(slow_moving_products) >= 5
            else [item["total_sales"] for item in slow_moving_products]
        ),
    }

    # Category-wise stock distribution
    category_stock_data = []
    for category in categories[:5]:  # Top 5 categories
        category_products = products.filter(category=category)
        total_quantity = sum([p.quantity for p in category_products])
        category_stock_data.append(
            {
                "name": category.name,
                "quantity": float(
                    total_quantity
                ),  # Convert Decimal to float for JSON serialization
            }
        )

    # Daily sales data (last 7 days)
    daily_sales_data = []
    for i in range(6, -1, -1):  # Last 7 days including today
        date_point = today - timedelta(days=i)
        day_sales = sales.filter(sale_date__date=date_point).count()
        daily_sales_data.append(
            {
                "date": date_point.strftime("%a"),  # Day name (Mon, Tue, etc.)
                "sales": day_sales,  # Number of sales
                "value": float(
                    sales.filter(sale_date__date=date_point).aggregate(
                        total_value=Sum("total_amount")
                    )["total_value"]
                    or 0
                ),  # Actual sales value
            }
        )

    # Top selling products (based on actual sales data)
    top_selling_products_real = []
    for item in product_sales_data[:5]:
        top_selling_products_real.append(
            {"name": item["product__name"], "sales": item["total_sales"]}
        )

    # If we don't have enough real data, pad with empty entries
    while len(top_selling_products_real) < 5:
        top_selling_products_real.append({"name": "No data", "sales": 0})

    # Convert data to JSON for JavaScript
    fast_slow_products_json = json.dumps(fast_slow_products_data)

    category_stock_json = json.dumps(
        [
            {"name": item["name"], "quantity": item["quantity"]}
            for item in category_stock_data
        ]
    )

    daily_sales_json = json.dumps(daily_sales_data)
    top_selling_json = json.dumps(top_selling_products_real)

    # Get recent activities (audit logs) for the current business
    recent_activities = (
        AuditLog.objects.filter(business=current_business)
        .select_related("user")
        .order_by("-timestamp")[:5]
    )

    context = {
        "total_products": total_products,
        "total_categories": total_categories,
        "total_sales": total_sales,
        "total_customers": total_customers,
        "total_purchases": total_purchases,
        "todays_sales_count": today_sales,  # Changed to match template variable name
        "todays_sales_amount": float(today_sales_amount),  # Add today's sales amount
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "product_value_in_stock": float(
            product_value_in_stock
        ),  # Convert Decimal to float
        "today_profit": float(today_profit),  # Convert Decimal to float
        "total_profit": float(total_profit),  # Convert Decimal to float
        "profit_margin": round(profit_margin, 1),  # Add profit margin to context
        "inventory_turnover": round(
            inventory_turnover, 1
        ),  # Add inventory turnover to context
        "customer_retention": round(
            customer_retention, 1
        ),  # Add customer retention to context
        "order_fulfillment": round(
            order_fulfillment, 1
        ),  # Add order fulfillment to context
        "low_stock_products": low_stock_products[:5],  # Limit to 5 for display
        "current_business": current_business,
        "recent_activities": recent_activities,  # Add recent activities to context
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
def owner_dashboard_view(request):
    """Owner dashboard view for business owners with multiple businesses"""
    # Check if user is a business owner
    if not hasattr(request.user, "owned_businesses"):
        messages.error(request, "You don't have access to the owner dashboard.")
        return redirect("dashboard:index")

    # Get user's businesses
    user_businesses = request.user.owned_businesses.all()

    if not user_businesses.exists():
        messages.info(request, "You don't own any businesses yet.")
        return redirect("dashboard:index")

    # Calculate aggregate metrics
    total_businesses = user_businesses.count()
    total_users = 0
    total_revenue = Decimal("0")
    total_sales = 0

    # For pending approvals, open tickets, and recent alerts, we need to calculate real data
    pending_approvals = 0
    open_tickets = 0
    recent_alerts = 0

    # Business status distribution counts
    active_count = 0
    pending_count = 0
    suspended_count = 0

    # Subscription plan distribution
    subscription_counts = {}

    for business in user_businesses:
        # Set current business context
        set_current_business(business)

        # Count users in this business
        total_users += (
            business.staff.count() + business.managers.count() + 1
        )  # +1 for owner

        # Calculate revenue for this business
        business_sales = Sale.objects.business_specific()
        total_sales += business_sales.count()

        # Calculate revenue
        for sale in business_sales:
            for item in sale.items.all():
                total_revenue += item.unit_price * item.quantity

        # Count pending approvals (purchase orders that need approval)
        from purchases.models import PurchaseOrder

        pending_approvals += (
            PurchaseOrder.objects.business_specific().filter(status="pending").count()
        )

        # Count open tickets (support tickets that are open)
        # Assuming there's a support ticket model, we'll use a placeholder for now
        # In a real implementation, this would connect to a support ticket system
        open_tickets += 0  # Placeholder - would connect to actual ticket system

        # Count recent alerts (stock alerts, etc.)
        from products.models import StockAlert

        recent_alerts += (
            StockAlert.objects.business_specific().filter(is_resolved=False).count()
        )

        # Count business status
        if business.status == "active":
            active_count += 1
        elif business.status == "pending":
            pending_count += 1
        elif business.status == "suspended":
            suspended_count += 1

        # Count subscription plans
        if business.subscription_plan:
            plan_name = business.subscription_plan.name
            subscription_counts[plan_name] = subscription_counts.get(plan_name, 0) + 1
        else:
            subscription_counts["Free"] = subscription_counts.get("Free", 0) + 1

    # Prepare business status data for chart
    business_status_labels = []
    business_status_data = []
    if active_count > 0:
        business_status_labels.append("Active")
        business_status_data.append(active_count)
    if pending_count > 0:
        business_status_labels.append("Pending")
        business_status_data.append(pending_count)
    if suspended_count > 0:
        business_status_labels.append("Suspended")
        business_status_data.append(suspended_count)

    # If no business status data, add at least one placeholder
    if not business_status_data:
        business_status_labels = ["No Data"]
        business_status_data = [1]

    # Prepare subscription plan data for chart
    subscription_labels = (
        list(subscription_counts.keys()) if subscription_counts else ["No Plans"]
    )
    subscription_data = (
        list(subscription_counts.values()) if subscription_counts else [1]
    )

    context = {
        "total_businesses": total_businesses,
        "total_users": total_users,
        "total_revenue": float(
            total_revenue
        ),  # Convert Decimal to float for JSON serialization
        "total_sales": total_sales,
        "pending_approvals": pending_approvals,
        "open_tickets": open_tickets,
        "recent_alerts": recent_alerts,
        "system_uptime": "99.9%",  # This is still a placeholder as it would require system monitoring
        # Business status chart data
        "business_status_labels": json.dumps(business_status_labels),
        "business_status_data": json.dumps(business_status_data),
        # Subscription plan chart data
        "subscription_labels": json.dumps(subscription_labels),
        "subscription_data": json.dumps(subscription_data),
        # Business list for table
        "user_businesses": user_businesses,
    }

    return render(request, "dashboard/owner_dashboard.html", context)


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

    # Search sales - Fixed the customer name search by using first_name and last_name fields
    sales = (
        Sale.objects.business_specific()
        .filter(
            Q(customer__first_name__icontains=query)
            | Q(customer__last_name__icontains=query)
            | Q(customer__phone__icontains=query)
            | Q(transaction_id__icontains=query)
        )
        .select_related("customer")
    )

    # Search customers
    customers = Customer.objects.business_specific().filter(
        Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
        | Q(email__icontains=query)
        | Q(phone__icontains=query)
    )

    # Search suppliers
    suppliers = Supplier.objects.business_specific().filter(
        Q(name__icontains=query)
        | Q(email__icontains=query)
        | Q(phone__icontains=query)
        | Q(company__icontains=query)
    )

    # Search categories
    categories = Category.objects.business_specific().filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    )

    context = {
        "query": query,
        "results": {
            "products": products,
            "sales": sales,
            "customers": customers,
            "suppliers": suppliers,
            "categories": categories,
        },
    }

    return render(request, "dashboard/search_results.html", context)


@login_required
def switch_branch_view(request):
    """
    Handle branch switching for multi-branch businesses
    """
    if request.method == "POST":
        branch_id = request.POST.get("branch_id")

        if branch_id:
            try:
                if branch_id == "main":
                    # Clear branch context to use main business
                    if "current_branch_id" in request.session:
                        del request.session["current_branch_id"]
                    messages.success(request, "Switched to main business location")
                else:
                    # Set specific branch
                    from superadmin.models import Branch

                    branch = Branch.objects.get(id=branch_id)
                    request.session["current_branch_id"] = branch.id
                    messages.success(request, f"Switched to branch: {branch.name}")
            except Exception as e:
                messages.error(request, f"Error switching branch: {str(e)}")
        else:
            messages.error(request, "Invalid branch selection")

    return redirect("dashboard:index")
