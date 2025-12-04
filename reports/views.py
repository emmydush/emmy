from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Q, Count
from products.models import Product, StockMovement, StockAlert, InventoryTransfer
from sales.models import Sale, SaleItem
from expenses.models import Expense
from customers.models import Customer
from suppliers.models import Supplier
from superadmin.models import Branch
from datetime import datetime, timedelta
from django.utils import timezone
import json
from decimal import Decimal
import csv
from django.http import HttpResponse
from authentication.utils import check_user_permission


@login_required
def report_list(request):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_access_reports"
    ):
        messages.error(request, "You do not have permission to access reports.")
        return redirect("dashboard:index")

    # Get current business and branch from middleware
    from superadmin.middleware import get_current_business, get_current_branch

    current_business = get_current_business()
    current_branch = get_current_branch()

    # Get all branches for this business
    branches = (
        Branch.objects.filter(business=current_business, is_active=True)
        if current_business
        else Branch.objects.none()
    )

    context = {
        "current_branch": current_branch,
        "branches": branches,
    }

    return render(request, "reports/list.html", context)


def get_date_ranges():
    """Get predefined date ranges for quick reporting"""
    today = timezone.now().date()

    # Daily
    daily_start = today
    daily_end = today

    # Weekly (Monday to Sunday)
    days_since_monday = today.weekday()
    weekly_start = today - timedelta(days=days_since_monday)
    weekly_end = weekly_start + timedelta(days=6)

    # Monthly
    monthly_start = today.replace(day=1)
    if today.month == 12:
        monthly_end = today.replace(day=31)
    else:
        next_month = today.replace(day=1, month=today.month + 1)
        monthly_end = next_month - timedelta(days=1)

    # Yearly
    yearly_start = today.replace(month=1, day=1)
    yearly_end = today.replace(month=12, day=31)

    return {
        "daily": {"start": daily_start, "end": daily_end},
        "weekly": {"start": weekly_start, "end": weekly_end},
        "monthly": {"start": monthly_start, "end": monthly_end},
        "yearly": {"start": yearly_start, "end": yearly_end},
    }


@login_required
def quick_report(request, period):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_access_reports"
    ):
        messages.error(request, "You do not have permission to access reports.")
        return redirect("dashboard:index")

    """Generate a quick report for predefined periods"""
    date_ranges = get_date_ranges()

    if period not in date_ranges:
        period = "monthly"  # Default to monthly

    start_date = date_ranges[period]["start"]
    end_date = date_ranges[period]["end"]

    # Get current branch from middleware if specified
    from superadmin.middleware import get_current_branch

    current_branch = get_current_branch()
    branch_id = request.GET.get("branch_id")

    # If branch_id is provided in GET parameters, use that branch
    if branch_id:
        try:
            selected_branch = Branch.objects.get(id=branch_id)
            # Override current branch context
            current_branch = selected_branch
        except Branch.DoesNotExist:
            messages.error(request, "Invalid branch selected.")
            selected_branch = None
    else:
        selected_branch = current_branch

    # Get sales data
    sales_queryset = Sale.objects.business_specific()
    if selected_branch:
        sales_queryset = sales_queryset.filter(branch=selected_branch)
    sales = sales_queryset.filter(
        sale_date__date__gte=start_date, sale_date__date__lte=end_date
    )

    total_sales = sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
    total_orders = sales.count()

    # Get expenses data
    expenses_queryset = Expense.objects.business_specific()
    if selected_branch:
        expenses_queryset = expenses_queryset.filter(branch=selected_branch)
    expenses = expenses_queryset.filter(date__gte=start_date, date__lte=end_date)
    total_expenses = expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    # Calculate profit
    # For simplicity, we'll use a rough estimate of COGS as 60% of sales
    estimated_cogs = total_sales * Decimal("0.6")
    gross_profit = total_sales - estimated_cogs
    net_profit = gross_profit - total_expenses

    # Get top selling products
    sale_items_queryset = SaleItem.objects.business_specific()
    if selected_branch:
        sale_items_queryset = sale_items_queryset.filter(sale__branch=selected_branch)
    top_products = (
        sale_items_queryset.filter(
            sale__sale_date__date__gte=start_date, sale__sale_date__date__lte=end_date
        )
        .values("product__name")
        .annotate(total_sold=Sum("quantity"), total_revenue=Sum("total_price"))
        .order_by("-total_sold")[:5]
    )

    # Generate recommendations based on the data
    recommendations = generate_recommendations(
        period,
        float(total_sales),
        total_orders,
        float(total_expenses),
        float(net_profit),
        top_products,
    )

    # Check if export is requested
    if "export" in request.GET and request.GET["export"] == "csv":
        return export_quick_report_csv(
            request,
            period,
            start_date,
            end_date,
            float(total_sales),
            total_orders,
            float(total_expenses),
            float(net_profit),
            top_products,
            recommendations,
        )

    # Get business settings
    from settings.models import BusinessSettings

    business_settings, created = BusinessSettings.objects.get_or_create(id=1)

    # Get current business and all branches for navigation
    from superadmin.middleware import get_current_business

    current_business = get_current_business()
    branches = (
        Branch.objects.filter(business=current_business, is_active=True)
        if current_business
        else Branch.objects.none()
    )

    context = {
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "total_sales": float(total_sales),
        "total_orders": total_orders,
        "total_expenses": float(total_expenses),
        "gross_profit": float(gross_profit),
        "net_profit": float(net_profit),
        "top_products": top_products,
        "recommendations": recommendations,
        "business_settings": business_settings,
        "current_branch": selected_branch,
        "branches": branches,
    }

    return render(request, "reports/quick_report.html", context)


def generate_recommendations(
    period, total_sales, total_orders, total_expenses, net_profit, top_products
):
    """Generate business recommendations based on report data"""
    recommendations = []

    # Sales recommendations
    if total_orders > 0:
        avg_order_value = total_sales / total_orders
        if avg_order_value < 50:
            recommendations.append(
                {
                    "type": "sales",
                    "priority": "medium",
                    "title": "Low Average Order Value",
                    "description": f"Your average order value is ${avg_order_value:.2f}. Consider upselling or bundling products to increase this.",
                    "action": "Implement upselling techniques and product bundles.",
                }
            )
        elif avg_order_value > 200:
            recommendations.append(
                {
                    "type": "sales",
                    "priority": "positive",
                    "title": "High Average Order Value",
                    "description": f"Great job! Your average order value is ${avg_order_value:.2f}, which is above industry standards.",
                    "action": "Maintain current strategies and look for opportunities to increase further.",
                }
            )

    # Profitability recommendations
    if total_sales > 0:
        profit_margin = (net_profit / total_sales) * 100
        if profit_margin < 10:
            recommendations.append(
                {
                    "type": "profitability",
                    "priority": "high",
                    "title": "Low Profit Margin",
                    "description": f"Your profit margin is {profit_margin:.1f}%. Consider reviewing your pricing strategy or cost structure.",
                    "action": "Analyze costs and consider adjusting prices or negotiating with suppliers.",
                }
            )
        elif profit_margin > 25:
            recommendations.append(
                {
                    "type": "profitability",
                    "priority": "positive",
                    "title": "Healthy Profit Margin",
                    "description": f"Excellent! Your profit margin is {profit_margin:.1f}%, indicating strong financial health.",
                    "action": "Continue monitoring to maintain this level of profitability.",
                }
            )

    # Expense recommendations
    if total_sales > 0:
        expense_ratio = (total_expenses / total_sales) * 100
        if expense_ratio > 30:
            recommendations.append(
                {
                    "type": "expenses",
                    "priority": "high",
                    "title": "High Expense Ratio",
                    "description": f"Expenses account for {expense_ratio:.1f}% of sales. Review discretionary spending.",
                    "action": "Identify areas to reduce costs without impacting core operations.",
                }
            )

    # Product recommendations
    if top_products:
        top_product = top_products[0] if top_products else None
        if top_product and top_product["total_sold"] > total_orders * 0.4:
            recommendations.append(
                {
                    "type": "products",
                    "priority": "medium",
                    "title": "Product Concentration Risk",
                    "description": f'{top_product["product__name"]} represents over 40% of sales. Consider diversifying your product range.',
                    "action": "Expand product offerings to reduce dependency on single products.",
                }
            )

    # Time-based recommendations
    if period == "daily" and total_sales == 0:
        recommendations.append(
            {
                "type": "operations",
                "priority": "high",
                "title": "No Sales Today",
                "description": "No sales recorded for today. Check if this is a reporting issue or operational concern.",
                "action": "Verify POS systems and consider promotional activities to drive sales.",
            }
        )

    return recommendations


def export_quick_report_csv(
    request,
    period,
    start_date,
    end_date,
    total_sales,
    total_orders,
    total_expenses,
    net_profit,
    top_products,
    recommendations,
):
    """Export quick report data to CSV with recommendations"""
    import csv
    from django.http import HttpResponse
    from io import StringIO

    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="quick_{period}_report_{start_date}_to_{end_date}.csv"'
    )

    writer = csv.writer(response)

    # Write header
    writer.writerow(
        [f"Quick {period.capitalize()} Report", f"From {start_date} to {end_date}"]
    )
    writer.writerow([])

    # Write summary data
    writer.writerow(["Summary"])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Sales", f"${total_sales:.2f}"])
    writer.writerow(["Total Orders", total_orders])
    writer.writerow(["Total Expenses", f"${total_expenses:.2f}"])
    writer.writerow(["Net Profit", f"${net_profit:.2f}"])
    writer.writerow([])

    # Write top selling products
    writer.writerow(["Top Selling Products"])
    writer.writerow(["Product", "Quantity Sold", "Revenue"])
    for product in top_products:
        writer.writerow(
            [
                product["product__name"],
                product["total_sold"],
                f"${product['total_revenue']:.2f}",
            ]
        )
    writer.writerow([])

    # Write recommendations
    writer.writerow(["Business Recommendations"])
    writer.writerow(
        ["Priority", "Category", "Title", "Description", "Suggested Action"]
    )
    for rec in recommendations:
        priority = rec.get("priority", "medium")
        priority_label = {
            "high": "HIGH",
            "medium": "MEDIUM",
            "low": "LOW",
            "positive": "POSITIVE",
        }.get(priority, "MEDIUM")

        writer.writerow(
            [
                priority_label,
                rec.get("type", "general").title(),
                rec.get("title", ""),
                rec.get("description", ""),
                rec.get("action", ""),
            ]
        )

    return response


@login_required
def sales_report(request):
    # Get date range from request or use defaults
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    if "start_date" in request.GET and request.GET["start_date"]:
        start_date = datetime.strptime(request.GET["start_date"], "%Y-%m-%d").date()
    if "end_date" in request.GET and request.GET["end_date"]:
        end_date = datetime.strptime(request.GET["end_date"], "%Y-%m-%d").date()

    # Get current branch from middleware if specified
    from superadmin.middleware import get_current_branch

    current_branch = get_current_branch()
    branch_id = request.GET.get("branch_id")

    # If branch_id is provided in GET parameters, use that branch
    if branch_id:
        try:
            selected_branch = Branch.objects.get(id=branch_id)
            # Override current branch context
            current_branch = selected_branch
        except Branch.DoesNotExist:
            messages.error(request, "Invalid branch selected.")
            selected_branch = None
    else:
        selected_branch = current_branch

    # Get current business from middleware
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    # Filter sales by branch if specified
    sales_queryset = Sale.objects.business_specific()
    if selected_branch:
        sales_queryset = sales_queryset.filter(branch=selected_branch)

    sales = sales_queryset.filter(
        sale_date__date__gte=start_date, sale_date__date__lte=end_date
    )

    # Group sales by date for chart data
    daily_sales = (
        sales.extra(select={"date": "date(sale_date)"})
        .values("date")
        .annotate(total=Sum("total_amount"), count=Count("id"))
        .order_by("date")
    )

    # Calculate totals
    total_sales = sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
    total_orders = sales.count()

    # Get top selling products
    sale_items_queryset = SaleItem.objects.business_specific()
    if selected_branch:
        sale_items_queryset = sale_items_queryset.filter(sale__branch=selected_branch)

    top_products = (
        sale_items_queryset.filter(
            sale__sale_date__date__gte=start_date, sale__sale_date__date__lte=end_date
        )
        .values("product__name")
        .annotate(total_sold=Sum("quantity"), total_revenue=Sum("total_price"))
        .order_by("-total_sold")[:10]
    )

    # Get hourly sales data for peak hours analysis
    hourly_sales = (
        sales.extra(select={"hour": "extract(hour from sale_date)"})
        .values("hour")
        .annotate(count=Count("id"), total=Sum("total_amount"))
        .order_by("hour")
    )

    # Get business settings
    from settings.models import BusinessSettings

    business_settings, created = BusinessSettings.objects.get_or_create(id=1)

    # Get all branches for branch selection dropdown
    branches = (
        Branch.objects.filter(business=current_business, is_active=True)
        if current_business
        else Branch.objects.none()
    )

    context = {
        "sales": sales,
        "daily_sales": daily_sales,
        "hourly_sales": hourly_sales,
        "total_sales": float(total_sales),
        "total_orders": total_orders,
        "top_products": top_products,
        "start_date": start_date,
        "end_date": end_date,
        "business_settings": business_settings,
        "current_branch": selected_branch,
        "branches": branches,
    }

    # Check if export is requested
    if "export" in request.GET and request.GET["export"] == "csv":
        return export_sales_report_csv(request, context)

    return render(request, "reports/sales.html", context)


def export_sales_report_csv(request, context):
    """Export sales report data to CSV with recommendations"""
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="sales_report_{context["start_date"]}_to_{context["end_date"]}.csv"'
    )

    writer = csv.writer(response)

    # Write header
    writer.writerow(
        ["Sales Report", f"From {context['start_date']} to {context['end_date']}"]
    )
    writer.writerow([])

    # Write sales data
    writer.writerow(["Sales"])
    writer.writerow(["ID", "Date", "Customer", "Total Amount"])
    for sale in context["sales"]:
        writer.writerow(
            [
                sale.id,
                sale.sale_date.strftime("%Y-%m-%d"),
                sale.customer.name if sale.customer else "Walk-in",
                f"${float(sale.total_amount):.2f}",
            ]
        )

    writer.writerow([])

    # Write daily sales summary
    writer.writerow(["Daily Sales"])
    writer.writerow(["Date", "Total Sales", "Total Orders"])
    for item in context["daily_sales"]:
        writer.writerow(
            [
                item["date"],
                f"${float(item['total']):.2f}",
                item["count"],
            ]
        )

    writer.writerow([])

    # Write top selling products
    writer.writerow(["Top Selling Products"])
    writer.writerow(["Product", "Quantity Sold", "Total Revenue"])
    for product in context["top_products"]:
        writer.writerow(
            [
                product["product__name"],
                product["total_sold"],
                f"${float(product['total_revenue']):.2f}",
            ]
        )

    return response


@login_required
def inventory_report(request):
    # Get date range from request or use defaults
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    if "start_date" in request.GET and request.GET["start_date"]:
        start_date = datetime.strptime(request.GET["start_date"], "%Y-%m-%d").date()
    if "end_date" in request.GET and request.GET["end_date"]:
        end_date = datetime.strptime(request.GET["end_date"], "%Y-%m-%d").date()

    # Get current branch from middleware if specified
    from superadmin.middleware import get_current_branch

    current_branch = get_current_branch()
    branch_id = request.GET.get("branch_id")

    # If branch_id is provided in GET parameters, use that branch
    if branch_id:
        try:
            selected_branch = Branch.objects.get(id=branch_id)
            # Override current branch context
            current_branch = selected_branch
        except Branch.DoesNotExist:
            messages.error(request, "Invalid branch selected.")
            selected_branch = None
    else:
        selected_branch = current_branch

    # Get current business from middleware
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    # Get products with low stock
    products_queryset = Product.objects.business_specific()
    if selected_branch:
        products_queryset = products_queryset.filter(branch=selected_branch)

    low_stock_products = products_queryset.filter(
        quantity__lte=F("reorder_level")
    ).order_by("quantity")

    # Get stock movements
    stock_movements_queryset = StockMovement.objects.business_specific()
    if selected_branch:
        stock_movements_queryset = stock_movements_queryset.filter(
            product__branch=selected_branch
        )

    recent_movements = (
        stock_movements_queryset.filter(
            created_at__date__gte=start_date, created_at__date__lte=end_date
        )
        .select_related("product", "created_by")
        .order_by("-created_at")[:50]
    )

    # Get stock alerts
    stock_alerts_queryset = StockAlert.objects.business_specific()
    if selected_branch:
        stock_alerts_queryset = stock_alerts_queryset.filter(
            product__branch=selected_branch
        )

    recent_alerts = (
        stock_alerts_queryset.filter(
            created_at__date__gte=start_date, created_at__date__lte=end_date
        )
        .select_related("product")
        .order_by("-created_at")[:20]
    )

    # Get inventory transfers
    transfers_queryset = InventoryTransfer.objects.business_specific()
    if selected_branch:
        # Show transfers where this branch is either source or destination
        transfers_queryset = transfers_queryset.filter(
            Q(from_branch=selected_branch) | Q(to_branch=selected_branch)
        )

    recent_transfers = (
        transfers_queryset.filter(
            created_at__date__gte=start_date, created_at__date__lte=end_date
        )
        .select_related(
            "from_branch", "to_branch", "product", "product_variant", "created_by"
        )
        .order_by("-created_at")[:20]
    )

    # Calculate inventory statistics
    total_products = products_queryset.count()
    low_stock_count = low_stock_products.count()

    # Calculate total inventory value
    inventory_value = products_queryset.aggregate(
        total_value=Sum(F("quantity") * F("cost_price"))
    )["total_value"] or Decimal("0")

    # Get business settings
    from settings.models import BusinessSettings

    business_settings, created = BusinessSettings.objects.get_or_create(id=1)

    # Get all branches for branch selection dropdown
    branches = (
        Branch.objects.filter(business=current_business, is_active=True)
        if current_business
        else Branch.objects.none()
    )

    context = {
        "low_stock_products": low_stock_products,
        "recent_movements": recent_movements,
        "recent_alerts": recent_alerts,
        "recent_transfers": recent_transfers,
        "total_products": total_products,
        "low_stock_count": low_stock_count,
        "inventory_value": float(inventory_value),
        "start_date": start_date,
        "end_date": end_date,
        "business_settings": business_settings,
        "current_branch": selected_branch,
        "branches": branches,
    }

    # Check if export is requested
    if "export" in request.GET and request.GET["export"] == "csv":
        return export_inventory_report_csv(request, context)

    return render(request, "reports/inventory.html", context)


def export_inventory_report_csv(request, context):
    """Export inventory report data to CSV with recommendations"""
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="inventory_report.csv"'

    writer = csv.writer(response)

    # Write header
    writer.writerow(["Inventory Report"])
    writer.writerow([])

    # Write low stock products
    writer.writerow(["Low Stock Products (Below Reorder Level)"])
    writer.writerow(["Product", "SKU", "Current Stock", "Reorder Level", "Category"])

    low_stock_products = (
        Product.objects.business_specific()
        .filter(quantity__lte=F("reorder_level"), is_active=True)
        .select_related("category")
    )

    for product in low_stock_products:
        writer.writerow(
            [
                product.name,
                product.sku,
                product.quantity,
                product.reorder_level,
                product.category.name if product.category else "",
            ]
        )

    writer.writerow([])

    # Write out of stock products
    writer.writerow(["Out of Stock Products"])
    writer.writerow(["Product", "SKU", "Category"])

    out_of_stock_products = (
        Product.objects.business_specific()
        .filter(quantity=0, is_active=True)
        .select_related("category")
    )

    for product in out_of_stock_products:
        writer.writerow(
            [
                product.name,
                product.sku,
                product.category.name if product.category else "",
            ]
        )

    writer.writerow([])

    # Write expired products
    writer.writerow(["Expired Products"])
    writer.writerow(["Product", "SKU", "Expiry Date", "Current Stock", "Category"])

    today = timezone.now().date()
    expired_products = (
        Product.objects.business_specific()
        .filter(expiry_date__lt=today, is_active=True)
        .select_related("category")
    )

    for product in expired_products:
        writer.writerow(
            [
                product.name,
                product.sku,
                product.expiry_date,
                product.quantity,
                product.category.name if product.category else "",
            ]
        )

    return response


@login_required
def profit_loss_report(request):
    # Get date range from request or use defaults
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    if "start_date" in request.GET and request.GET["start_date"]:
        start_date = datetime.strptime(request.GET["start_date"], "%Y-%m-%d").date()
    if "end_date" in request.GET and request.GET["end_date"]:
        end_date = datetime.strptime(request.GET["end_date"], "%Y-%m-%d").date()

    # Get current branch from middleware if specified
    from superadmin.middleware import get_current_branch

    current_branch = get_current_branch()
    branch_id = request.GET.get("branch_id")

    # If branch_id is provided in GET parameters, use that branch
    if branch_id:
        try:
            selected_branch = Branch.objects.get(id=branch_id)
            # Override current branch context
            current_branch = selected_branch
        except Branch.DoesNotExist:
            messages.error(request, "Invalid branch selected.")
            selected_branch = None
    else:
        selected_branch = current_branch

    # Get current business from middleware
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    # Get sales data
    sales_queryset = Sale.objects.business_specific()
    if selected_branch:
        sales_queryset = sales_queryset.filter(branch=selected_branch)

    sales = sales_queryset.filter(
        sale_date__date__gte=start_date, sale_date__date__lte=end_date
    )

    # Get expenses data
    expenses_queryset = Expense.objects.business_specific()
    if selected_branch:
        expenses_queryset = expenses_queryset.filter(branch=selected_branch)

    expenses = expenses_queryset.filter(date__gte=start_date, date__lte=end_date)

    # Calculate sales totals
    total_sales = sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
    total_orders = sales.count()

    # Calculate expense totals
    total_expenses = expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    expense_count = expenses.count()

    # Calculate profit metrics
    # For simplicity, we'll use a rough estimate of COGS as 60% of sales
    estimated_cogs = total_sales * Decimal("0.6")
    gross_profit = total_sales - estimated_cogs
    net_profit = gross_profit - total_expenses

    # Calculate profit margins
    profit_margin = (
        (float(net_profit) / float(total_sales) * 100) if float(total_sales) > 0 else 0
    )
    gross_profit_margin = (
        (float(gross_profit) / float(total_sales) * 100)
        if float(total_sales) > 0
        else 0
    )

    # Group sales by date for chart data
    daily_sales = (
        sales.extra(select={"date": "date(sale_date)"})
        .values("date")
        .annotate(total=Sum("total_amount"))
        .order_by("date")
    )

    # Group expenses by category
    expense_categories = (
        expenses.values("category")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )

    # Get top selling products
    sale_items_queryset = SaleItem.objects.business_specific()
    if selected_branch:
        sale_items_queryset = sale_items_queryset.filter(sale__branch=selected_branch)

    top_products = (
        sale_items_queryset.filter(
            sale__sale_date__date__gte=start_date, sale__sale_date__date__lte=end_date
        )
        .values("product__name")
        .annotate(total_sold=Sum("quantity"), total_revenue=Sum("total_price"))
        .order_by("-total_revenue")[:10]
    )

    # Get business settings
    from settings.models import BusinessSettings

    business_settings, created = BusinessSettings.objects.get_or_create(id=1)

    # Get all branches for branch selection dropdown
    branches = (
        Branch.objects.filter(business=current_business, is_active=True)
        if current_business
        else Branch.objects.none()
    )

    context = {
        "total_sales": float(total_sales),
        "total_orders": total_orders,
        "total_expenses": float(total_expenses),
        "expense_count": expense_count,
        "estimated_cogs": float(estimated_cogs),
        "gross_profit": float(gross_profit),
        "net_profit": float(net_profit),
        "profit_margin": profit_margin,
        "gross_profit_margin": gross_profit_margin,
        "daily_sales": daily_sales,
        "expense_categories": expense_categories,
        "top_products": top_products,
        "start_date": start_date,
        "end_date": end_date,
        "business_settings": business_settings,
        "current_branch": selected_branch,
        "branches": branches,
    }

    # Check if export is requested
    if "export" in request.GET and request.GET["export"] == "csv":
        return export_profit_loss_report_csv(request, context)

    return render(request, "reports/profit_loss.html", context)


def export_profit_loss_report_csv(request, context):
    """Export profit/loss report data to CSV"""
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="profit_loss_report_{context["start_date"]}_to_{context["end_date"]}.csv"'
    )

    writer = csv.writer(response)

    # Write header
    writer.writerow(
        [
            "Profit & Loss Report",
            f"From {context['start_date']} to {context['end_date']}",
        ]
    )
    writer.writerow([])

    # Write summary data
    writer.writerow(["Financial Summary"])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Sales Revenue", f"${context['total_sales']:.2f}"])
    writer.writerow(["Number of Orders", context["total_orders"]])
    writer.writerow(["Operating Expenses", f"${context['total_expenses']:.2f}"])
    writer.writerow(["Expense Entries", context["expense_count"]])
    writer.writerow(["Estimated COGS", f"${context['estimated_cogs']:.2f}"])
    writer.writerow(["Gross Profit", f"${context['gross_profit']:.2f}"])
    writer.writerow(["Net Profit", f"${context['net_profit']:.2f}"])
    writer.writerow(["Gross Profit Margin", f"{context['gross_profit_margin']:.2f}%"])
    writer.writerow(["Net Profit Margin", f"{context['profit_margin']:.2f}%"])
    writer.writerow([])

    # Write daily sales data
    writer.writerow(["Daily Sales"])
    writer.writerow(["Date", "Total Sales"])
    for item in context["daily_sales"]:
        writer.writerow([item["date"], f"${float(item['total']):.2f}"])
    writer.writerow([])

    # Write expenses by category
    writer.writerow(["Expenses by Category"])
    writer.writerow(["Category", "Total Amount", "Number of Entries"])
    for category in context["expense_categories"]:
        writer.writerow(
            [
                category["category"] or "Uncategorized",
                f"${float(category['total']):.2f}",
                category["count"],
            ]
        )
    writer.writerow([])

    # Write top selling products
    writer.writerow(["Top Selling Products"])
    writer.writerow(["Product", "Quantity Sold", "Total Revenue"])
    for product in context["top_products"]:
        writer.writerow(
            [
                product["product__name"],
                product["total_sold"],
                f"${float(product['total_revenue']):.2f}",
            ]
        )

    return response


def export_expenses_report_csv(request, context):
    """Export expenses report data to CSV"""
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="expenses_report_{context["start_date"]}_to_{context["end_date"]}.csv"'
    )

    writer = csv.writer(response)

    # Write header
    writer.writerow(
        ["Expenses Report", f"From {context['start_date']} to {context['end_date']}"]
    )
    writer.writerow([])

    # Write summary data
    writer.writerow(["Summary"])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Expenses", f"${context['total_expenses']:.2f}"])
    writer.writerow(["Number of Expenses", context["expense_count"]])
    writer.writerow([])

    # Write expenses by category
    writer.writerow(["Expenses by Category"])
    writer.writerow(["Category", "Total Amount", "Number of Expenses"])
    for category in context["expense_categories"]:
        writer.writerow(
            [
                category["category"] or "Uncategorized",
                f"${float(category['total']):.2f}",
                category["count"],
            ]
        )
    writer.writerow([])

    # Write daily expenses
    writer.writerow(["Daily Expenses"])
    writer.writerow(["Date", "Total Amount"])
    for item in context["daily_expenses"]:
        writer.writerow([item["date"], f"${float(item['total']):.2f}"])
    writer.writerow([])

    # Write recent expenses
    writer.writerow(["Recent Expenses"])
    writer.writerow(["Date", "Category", "Description", "Amount", "Branch"])
    for expense in context["recent_expenses"]:
        writer.writerow(
            [
                expense.date.strftime("%Y-%m-%d") if expense.date else "",
                expense.category.name if expense.category else "Uncategorized",
                expense.description,
                f"${float(expense.amount):.2f}",
                expense.branch.name if expense.branch else "",
            ]
        )

    return response


def export_profit_loss_report_csv_with_recommendations(request, start_date, end_date):
    """Export profit & loss report data to CSV with recommendations"""
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="profit_loss_report_{start_date}_to_{end_date}.csv"'
    )

    writer = csv.writer(response)

    # Write header
    writer.writerow(["Profit & Loss Report", f"From {start_date} to {end_date}"])
    writer.writerow([])

    # Calculate sales revenue
    sales = Sale.objects.business_specific().filter(
        sale_date__date__gte=start_date, sale_date__date__lte=end_date
    )
    sales_revenue = sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")

    # Calculate cost of goods sold (COGS)
    sale_items = SaleItem.objects.business_specific().filter(
        sale__sale_date__date__gte=start_date, sale__sale_date__date__lte=end_date
    )

    cogs = Decimal("0")
    for item in sale_items:
        cogs += Decimal(str(item.product.cost_price)) * Decimal(str(item.quantity))

    # Calculate expenses
    expenses = Expense.objects.business_specific().filter(
        date__gte=start_date, date__lte=end_date
    )
    total_expenses = expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    # Calculate profit metrics
    gross_profit = sales_revenue - cogs
    net_profit = gross_profit - total_expenses

    # Calculate profit margins
    gross_profit_margin = (
        (float(gross_profit) / float(sales_revenue) * 100)
        if float(sales_revenue) > 0
        else 0
    )
    net_profit_margin = (
        (float(net_profit) / float(sales_revenue) * 100)
        if float(sales_revenue) > 0
        else 0
    )

    # Write summary data
    writer.writerow(["Financial Summary"])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Sales Revenue", f"${float(sales_revenue):.2f}"])
    writer.writerow(["Number of Orders", sales.count()])
    writer.writerow(["Operating Expenses", f"${float(total_expenses):.2f}"])
    writer.writerow(["Expense Entries", expenses.count()])
    writer.writerow(["Estimated COGS", f"${float(cogs):.2f}"])
    writer.writerow(["Gross Profit", f"${float(gross_profit):.2f}"])
    writer.writerow(["Net Profit", f"${float(net_profit):.2f}"])
    writer.writerow(["Gross Profit Margin", f"{gross_profit_margin:.2f}%"])
    writer.writerow(["Net Profit Margin", f"{net_profit_margin:.2f}%"])
    writer.writerow([])

    # Write monthly profit summary
    monthly_profit_summary = []
    current_month = start_date.replace(day=1)

    writer.writerow(["Monthly Profit Summary"])
    writer.writerow(
        ["Month", "Revenue", "COGS", "Gross Profit", "Expenses", "Net Profit"]
    )

    while current_month <= end_date:
        # Get last day of month
        if current_month.month == 12:
            next_month = current_month.replace(
                year=current_month.year + 1, month=1, day=1
            )
        else:
            next_month = current_month.replace(month=current_month.month + 1, day=1)

        month_end = next_month - timedelta(days=1)

        # Calculate monthly data
        monthly_sales = Sale.objects.business_specific().filter(
            sale_date__date__gte=current_month, sale_date__date__lte=month_end
        )
        monthly_revenue = monthly_sales.aggregate(total=Sum("total_amount"))[
            "total"
        ] or Decimal("0")

        monthly_items = SaleItem.objects.business_specific().filter(
            sale__sale_date__date__gte=current_month,
            sale__sale_date__date__lte=month_end,
        )
        monthly_cogs = Decimal("0")
        for monthly_item in monthly_items:
            monthly_cogs += Decimal(str(monthly_item.product.cost_price)) * Decimal(
                str(monthly_item.quantity)
            )

        monthly_expenses = Expense.objects.business_specific().filter(
            date__gte=current_month, date__lte=month_end
        )
        monthly_expense_total = monthly_expenses.aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0")

        monthly_profit = monthly_revenue - monthly_cogs - monthly_expense_total

        writer.writerow(
            [
                current_month.strftime("%B %Y"),
                f"${float(monthly_revenue):.2f}",
                f"${float(monthly_cogs):.2f}",
                f"${float(monthly_revenue - monthly_cogs):.2f}",
                f"${float(monthly_expense_total):.2f}",
                f"${float(monthly_profit):.2f}",
            ]
        )

        # Move to next month
        if current_month.month == 12:
            current_month = current_month.replace(
                year=current_month.year + 1, month=1, day=1
            )
        else:
            current_month = current_month.replace(month=current_month.month + 1, day=1)

    writer.writerow([])

    # Generate and write recommendations
    recommendations = generate_profit_loss_recommendations(
        float(sales_revenue),
        float(cogs),
        float(total_expenses),
        float(gross_profit),
        float(net_profit),
        gross_profit_margin,
        net_profit_margin,
    )

    writer.writerow(["Business Recommendations"])
    writer.writerow(
        ["Priority", "Category", "Title", "Description", "Suggested Action"]
    )
    for rec in recommendations:
        priority = rec.get("priority", "medium")
        priority_label = {
            "high": "HIGH",
            "medium": "MEDIUM",
            "low": "LOW",
            "positive": "POSITIVE",
        }.get(priority, "MEDIUM")

        writer.writerow(
            [
                priority_label,
                rec.get("type", "general").title(),
                rec.get("title", ""),
                rec.get("description", ""),
                rec.get("action", ""),
            ]
        )

    return response


def generate_profit_loss_recommendations(
    sales_revenue,
    cogs,
    total_expenses,
    gross_profit,
    net_profit,
    gross_margin,
    net_margin,
):
    """Generate profit & loss specific recommendations"""
    recommendations = []

    # Profitability recommendations
    if net_margin < 5:
        recommendations.append(
            {
                "type": "profitability",
                "priority": "high",
                "title": "Low Profitability",
                "description": f"Net profit margin is {net_margin:.1f}%, which is below industry standards.",
                "action": "Review pricing strategy, reduce operating costs, and optimize product mix.",
            }
        )
    elif net_margin > 15:
        recommendations.append(
            {
                "type": "profitability",
                "priority": "positive",
                "title": "Strong Profitability",
                "description": f"Excellent net profit margin of {net_margin:.1f}%. This indicates strong financial performance.",
                "action": "Reinvest profits strategically to sustain growth while maintaining this level of profitability.",
            }
        )

    # Cost structure recommendations
    if sales_revenue > 0:
        cogs_ratio = (cogs / sales_revenue) * 100
        expense_ratio = (total_expenses / sales_revenue) * 100

        if cogs_ratio > 60:
            recommendations.append(
                {
                    "type": "cost_management",
                    "priority": "medium",
                    "title": "High COGS Ratio",
                    "description": f"Cost of goods sold represents {cogs_ratio:.1f}% of sales. This may impact profitability.",
                    "action": "Negotiate better supplier rates, review inventory management, and consider alternative suppliers.",
                }
            )

        if expense_ratio > 25:
            recommendations.append(
                {
                    "type": "cost_management",
                    "priority": "high",
                    "title": "High Operating Expenses",
                    "description": f"Operating expenses account for {expense_ratio:.1f}% of sales. This is relatively high.",
                    "action": "Review discretionary spending, consolidate services, and optimize operational efficiency.",
                }
            )

    # Break-even analysis
    if sales_revenue > 0 and total_expenses > 0:
        # Simplified break-even calculation
        bep = total_expenses / (gross_profit / sales_revenue) if gross_profit > 0 else 0
        if bep > sales_revenue * 1.2:
            recommendations.append(
                {
                    "type": "financial_health",
                    "priority": "high",
                    "title": "High Break-Even Point",
                    "description": "Current sales are close to the break-even point. Small changes could impact profitability.",
                    "action": "Increase sales volume, reduce fixed costs, or improve pricing strategy.",
                }
            )

    return recommendations


@login_required
def expenses_report(request):
    # Get date range from request or use defaults
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    if "start_date" in request.GET and request.GET["start_date"]:
        start_date = datetime.strptime(request.GET["start_date"], "%Y-%m-%d").date()
    if "end_date" in request.GET and request.GET["end_date"]:
        end_date = datetime.strptime(request.GET["end_date"], "%Y-%m-%d").date()

    # Get current branch from middleware if specified
    from superadmin.middleware import get_current_branch

    current_branch = get_current_branch()
    branch_id = request.GET.get("branch_id")

    # If branch_id is provided in GET parameters, use that branch
    if branch_id:
        try:
            selected_branch = Branch.objects.get(id=branch_id)
            # Override current branch context
            current_branch = selected_branch
        except Branch.DoesNotExist:
            messages.error(request, "Invalid branch selected.")
            selected_branch = None
    else:
        selected_branch = current_branch

    # Get current business from middleware
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    # Filter expenses by date range and branch
    expenses_queryset = Expense.objects.business_specific()
    if selected_branch:
        expenses_queryset = expenses_queryset.filter(branch=selected_branch)
    expenses = expenses_queryset.filter(date__gte=start_date, date__lte=end_date)

    # Calculate total expenses
    total_expenses = expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    expense_count = expenses.count()

    # Group expenses by category with count
    expense_by_category = (
        expenses.values("category__name")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )

    # Prepare data for expense trend chart
    expense_trend_data = (
        expenses.extra({"date": "date(date)"})
        .values("date")
        .annotate(total=Sum("amount"))
        .order_by("date")
    )

    # Fix: Handle the case where item['date'] might already be a string
    expense_dates = []
    expense_amounts = []

    for item in expense_trend_data:
        if isinstance(item["date"], str):
            # Already a string, use as is
            expense_dates.append(item["date"])
        else:
            # Convert date object to string
            expense_dates.append(item["date"].strftime("%Y-%m-%d"))
        expense_amounts.append(float(item["total"]))

    # Prepare data for category chart
    category_names = [item["category__name"] for item in expense_by_category]
    category_amounts = [float(item["total"]) for item in expense_by_category]

    # Convert to JSON for JavaScript
    expense_dates_json = json.dumps(expense_dates)
    expense_amounts_json = json.dumps(expense_amounts)
    category_names_json = json.dumps(category_names)
    category_amounts_json = json.dumps(category_amounts)

    # Get business settings
    from settings.models import BusinessSettings

    business_settings, created = BusinessSettings.objects.get_or_create(id=1)

    # Get all branches for branch selection dropdown
    branches = (
        Branch.objects.filter(business=current_business, is_active=True)
        if current_business
        else Branch.objects.none()
    )

    context = {
        "start_date": start_date,
        "end_date": end_date,
        "total_expenses": float(total_expenses),
        "expense_count": expense_count,
        "expense_by_category": expense_by_category,
        "expense_dates_json": expense_dates_json,
        "expense_amounts_json": expense_amounts_json,
        "category_names_json": category_names_json,
        "category_amounts_json": category_amounts_json,
        "business_settings": business_settings,
        "current_branch": selected_branch,
        "branches": branches,
    }

    # Check if export is requested
    if "export" in request.GET and request.GET["export"] == "csv":
        return export_expenses_report_csv(request, context)

    return render(request, "reports/expenses.html", context)


def generate_expense_recommendations(
    total_expenses, expense_by_category, expense_count
):
    """Generate expense-specific recommendations"""
    recommendations = []

    # Overall expense level recommendations
    if total_expenses > 10000:
        recommendations.append(
            {
                "type": "expense_level",
                "priority": "high",
                "title": "High Expense Level",
                "description": f"Total expenses of ${total_expenses:.2f} may be high for your business size.",
                "action": "Review all expense categories and identify areas for cost reduction.",
            }
        )
    elif total_expenses < 1000:
        recommendations.append(
            {
                "type": "expense_level",
                "priority": "positive",
                "title": "Efficient Expense Management",
                "description": f"Total expenses of ${total_expenses:.2f} appear to be well-controlled.",
                "action": "Continue monitoring expenses to maintain this level of efficiency.",
            }
        )

    # Category concentration recommendations
    if expense_by_category:
        top_category = expense_by_category[0] if expense_by_category else None
        if top_category and (float(top_category["total"]) / total_expenses) > 0.4:
            recommendations.append(
                {
                    "type": "expense_diversity",
                    "priority": "medium",
                    "title": "Expense Concentration Risk",
                    "description": f'Top expense category ({top_category["category__name"]}) represents over 40% of total expenses.',
                    "action": "Diversify expenses across categories and review if this concentration is necessary.",
                }
            )

    # Expense frequency recommendations
    if expense_count > 50:
        recommendations.append(
            {
                "type": "expense_frequency",
                "priority": "medium",
                "title": "High Expense Frequency",
                "description": f"{expense_count} expense entries recorded. This may indicate fragmented spending.",
                "action": "Consolidate similar expenses and review approval processes for small purchases.",
            }
        )

    return recommendations


# Centralized dashboard for multi-branch monitoring
@login_required
def multi_branch_dashboard(request):
    """Centralized dashboard showing performance across all branches"""
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_access_reports"
    ):
        messages.error(request, "You do not have permission to access reports.")
        return redirect("dashboard:index")

    # Get current business from middleware
    from superadmin.middleware import get_current_business

    current_business = get_current_business()

    if not current_business:
        messages.error(request, "No business context found.")
        return redirect("dashboard:index")

    # Get all active branches for this business
    branches = Branch.objects.filter(business=current_business, is_active=True)

    # Get date range (last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Collect branch performance data
    branch_performance = []
    total_sales_all_branches = Decimal("0")
    total_expenses_all_branches = Decimal("0")
    total_net_profit_all_branches = Decimal("0")

    for branch in branches:
        # Get sales data for this branch
        branch_sales = Sale.objects.filter(
            business=current_business,
            branch=branch,
            sale_date__date__gte=start_date,
            sale_date__date__lte=end_date,
        )

        branch_total_sales = branch_sales.aggregate(total=Sum("total_amount"))[
            "total"
        ] or Decimal("0")
        branch_total_orders = branch_sales.count()

        # Get expenses data for this branch
        branch_expenses = Expense.objects.filter(
            business=current_business,
            branch=branch,
            date__gte=start_date,
            date__lte=end_date,
        )
        branch_total_expenses = branch_expenses.aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0")

        # Calculate profit
        estimated_cogs = branch_total_sales * Decimal("0.6")
        branch_gross_profit = branch_total_sales - estimated_cogs
        branch_net_profit = branch_gross_profit - branch_total_expenses

        # Calculate profit margin
        profit_margin = (
            (float(branch_net_profit) / float(branch_total_sales) * 100)
            if float(branch_total_sales) > 0
            else 0
        )

        branch_performance.append(
            {
                "branch": branch,
                "total_sales": float(branch_total_sales),
                "total_orders": branch_total_orders,
                "total_expenses": float(branch_total_expenses),
                "net_profit": float(branch_net_profit),
                "profit_margin": profit_margin,
            }
        )

        total_sales_all_branches += branch_total_sales
        total_expenses_all_branches += branch_total_expenses
        total_net_profit_all_branches += branch_net_profit

    # Sort branches by sales performance
    branch_performance.sort(key=lambda x: x["total_sales"], reverse=True)

    # Get top selling products across all branches
    top_products = (
        SaleItem.objects.filter(
            sale__business=current_business,
            sale__sale_date__date__gte=start_date,
            sale__sale_date__date__lte=end_date,
        )
        .values("product__name")
        .annotate(total_sold=Sum("quantity"), total_revenue=Sum("total_price"))
        .order_by("-total_sold")[:10]
    )

    # Prepare data for charts
    branch_names = [item["branch"].name for item in branch_performance]
    branch_sales_data = [item["total_sales"] for item in branch_performance]
    branch_profit_data = [item["net_profit"] for item in branch_performance]

    # Convert to JSON for JavaScript
    branch_names_json = json.dumps(branch_names)
    branch_sales_json = json.dumps(branch_sales_data)
    branch_profit_json = json.dumps(branch_profit_data)

    # Top products data
    product_names = [item["product__name"] for item in top_products]
    product_quantities = [float(item["total_sold"]) for item in top_products]
    product_revenues = [float(item["total_revenue"]) for item in top_products]

    product_names_json = json.dumps(product_names)
    product_quantities_json = json.dumps(product_quantities)
    product_revenues_json = json.dumps(product_revenues)

    # Get business settings
    from settings.models import BusinessSettings

    business_settings, created = BusinessSettings.objects.get_or_create(id=1)

    context = {
        "branches": branches,
        "branch_performance": branch_performance,
        "total_sales_all_branches": float(total_sales_all_branches),
        "total_expenses_all_branches": float(total_expenses_all_branches),
        "total_net_profit": float(total_net_profit_all_branches),
        "start_date": start_date,
        "end_date": end_date,
        "top_products": top_products,
        "branch_names_json": branch_names_json,
        "branch_sales_json": branch_sales_json,
        "branch_profit_json": branch_profit_json,
        "product_names_json": product_names_json,
        "product_quantities_json": product_quantities_json,
        "product_revenues_json": product_revenues_json,
        "business_settings": business_settings,
    }

    return render(request, "reports/multi_branch_dashboard.html", context)


# Test charts view
def test_charts(request):
    """Test view to verify chart background removal"""
    from settings.models import BusinessSettings

    business_settings, created = BusinessSettings.objects.get_or_create(id=1)

    return render(
        request,
        "reports/test_charts.html",
        {
            "business_settings": business_settings,
        },
    )
