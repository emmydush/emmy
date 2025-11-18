from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Q, Count
from products.models import Product
from sales.models import Sale, SaleItem
from expenses.models import Expense
from customers.models import Customer
from suppliers.models import Supplier
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
    if request.user.role != 'admin' and not check_user_permission(request.user, 'can_access_reports'):
        messages.error(request, 'You do not have permission to access reports.')
        return redirect('dashboard:index')
        
    return render(request, 'reports/list.html')

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
        'daily': {'start': daily_start, 'end': daily_end},
        'weekly': {'start': weekly_start, 'end': weekly_end},
        'monthly': {'start': monthly_start, 'end': monthly_end},
        'yearly': {'start': yearly_start, 'end': yearly_end},
    }

@login_required
def quick_report(request, period):
    # Account owners have access to everything
    if request.user.role != 'admin' and not check_user_permission(request.user, 'can_access_reports'):
        messages.error(request, 'You do not have permission to access reports.')
        return redirect('dashboard:index')
        
    """Generate a quick report for predefined periods"""
    date_ranges = get_date_ranges()
    
    if period not in date_ranges:
        period = 'monthly'  # Default to monthly
    
    start_date = date_ranges[period]['start']
    end_date = date_ranges[period]['end']
    
    # Get sales data
    sales = Sale.objects.business_specific().filter(
        sale_date__date__gte=start_date, 
        sale_date__date__lte=end_date
    )
    
    total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    total_orders = sales.count()
    
    # Get expenses data
    expenses = Expense.objects.business_specific().filter(
        date__gte=start_date, 
        date__lte=end_date
    )
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Calculate profit
    # For simplicity, we'll use a rough estimate of COGS as 60% of sales
    estimated_cogs = total_sales * Decimal('0.6')
    gross_profit = total_sales - estimated_cogs
    net_profit = gross_profit - total_expenses
    
    # Get top selling products
    top_products = SaleItem.objects.business_specific().filter(
        sale__sale_date__date__gte=start_date,
        sale__sale_date__date__lte=end_date
    ).values('product__name').annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_sold')[:5]
    
    # Generate recommendations based on the data
    recommendations = generate_recommendations(
        period, 
        float(total_sales), 
        total_orders, 
        float(total_expenses), 
        float(net_profit),
        top_products
    )
    
    # Check if export is requested
    if 'export' in request.GET and request.GET['export'] == 'csv':
        return export_quick_report_csv(request, period, start_date, end_date, 
                                     float(total_sales), total_orders, 
                                     float(total_expenses), float(net_profit), 
                                     top_products, recommendations)
    
    # Get business settings
    from settings.models import BusinessSettings
    business_settings, created = BusinessSettings.objects.get_or_create(id=1)
    
    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': float(total_sales),
        'total_orders': total_orders,
        'total_expenses': float(total_expenses),
        'gross_profit': float(gross_profit),
        'net_profit': float(net_profit),
        'top_products': top_products,
        'recommendations': recommendations,
        'business_settings': business_settings,
    }
    
    return render(request, 'reports/quick_report.html', context)

def generate_recommendations(period, total_sales, total_orders, total_expenses, net_profit, top_products):
    """Generate business recommendations based on report data"""
    recommendations = []
    
    # Sales recommendations
    if total_orders > 0:
        avg_order_value = total_sales / total_orders
        if avg_order_value < 50:
            recommendations.append({
                'type': 'sales',
                'priority': 'medium',
                'title': 'Low Average Order Value',
                'description': f'Your average order value is ${avg_order_value:.2f}. Consider upselling or bundling products to increase this.',
                'action': 'Implement upselling techniques and product bundles.'
            })
        elif avg_order_value > 200:
            recommendations.append({
                'type': 'sales',
                'priority': 'positive',
                'title': 'High Average Order Value',
                'description': f'Great job! Your average order value is ${avg_order_value:.2f}, which is above industry standards.',
                'action': 'Maintain current strategies and look for opportunities to increase further.'
            })
    
    # Profitability recommendations
    if total_sales > 0:
        profit_margin = (net_profit / total_sales) * 100
        if profit_margin < 10:
            recommendations.append({
                'type': 'profitability',
                'priority': 'high',
                'title': 'Low Profit Margin',
                'description': f'Your profit margin is {profit_margin:.1f}%. Consider reviewing your pricing strategy or cost structure.',
                'action': 'Analyze costs and consider adjusting prices or negotiating with suppliers.'
            })
        elif profit_margin > 25:
            recommendations.append({
                'type': 'profitability',
                'priority': 'positive',
                'title': 'Healthy Profit Margin',
                'description': f'Excellent! Your profit margin is {profit_margin:.1f}%, indicating strong financial health.',
                'action': 'Continue monitoring to maintain this level of profitability.'
            })
    
    # Expense recommendations
    if total_sales > 0:
        expense_ratio = (total_expenses / total_sales) * 100
        if expense_ratio > 30:
            recommendations.append({
                'type': 'expenses',
                'priority': 'high',
                'title': 'High Expense Ratio',
                'description': f'Expenses account for {expense_ratio:.1f}% of sales. Review discretionary spending.',
                'action': 'Identify areas to reduce costs without impacting core operations.'
            })
    
    # Product recommendations
    if top_products:
        top_product = top_products[0] if top_products else None
        if top_product and top_product['total_sold'] > total_orders * 0.4:
            recommendations.append({
                'type': 'products',
                'priority': 'medium',
                'title': 'Product Concentration Risk',
                'description': f'{top_product["product__name"]} represents over 40% of sales. Consider diversifying your product range.',
                'action': 'Expand product offerings to reduce dependency on single products.'
            })
    
    # Time-based recommendations
    if period == 'daily' and total_sales == 0:
        recommendations.append({
            'type': 'operations',
            'priority': 'high',
            'title': 'No Sales Today',
            'description': 'No sales recorded for today. Check if this is a reporting issue or operational concern.',
            'action': 'Verify POS systems and consider promotional activities to drive sales.'
        })
    
    return recommendations

def export_quick_report_csv(request, period, start_date, end_date, total_sales, 
                          total_orders, total_expenses, net_profit, top_products, recommendations):
    """Export quick report data to CSV with recommendations"""
    import csv
    from django.http import HttpResponse
    from io import StringIO
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="quick_{period}_report_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([f'Quick {period.capitalize()} Report', f'From {start_date} to {end_date}'])
    writer.writerow([])
    
    # Write summary data
    writer.writerow(['Summary'])
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total Sales', f'${total_sales:.2f}'])
    writer.writerow(['Total Orders', total_orders])
    writer.writerow(['Total Expenses', f'${total_expenses:.2f}'])
    writer.writerow(['Net Profit', f'${net_profit:.2f}'])
    writer.writerow([])
    
    # Write top selling products
    writer.writerow(['Top Selling Products'])
    writer.writerow(['Product', 'Quantity Sold', 'Revenue'])
    for product in top_products:
        writer.writerow([
            product['product__name'], 
            product['total_sold'], 
            f"${product['total_revenue']:.2f}"
        ])
    writer.writerow([])
    
    # Write recommendations
    writer.writerow(['Business Recommendations'])
    writer.writerow(['Priority', 'Category', 'Title', 'Description', 'Suggested Action'])
    for rec in recommendations:
        priority = rec.get('priority', 'medium')
        priority_label = {
            'high': 'HIGH',
            'medium': 'MEDIUM',
            'low': 'LOW',
            'positive': 'POSITIVE'
        }.get(priority, 'MEDIUM')
        
        writer.writerow([
            priority_label,
            rec.get('type', 'general').title(),
            rec.get('title', ''),
            rec.get('description', ''),
            rec.get('action', '')
        ])
    
    return response

@login_required
def sales_report(request):
    # Get date range from request or use defaults
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if 'start_date' in request.GET and request.GET['start_date']:
        start_date = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
    if 'end_date' in request.GET and request.GET['end_date']:
        end_date = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
    
    # Check if export is requested
    if 'export' in request.GET and request.GET['export'] == 'csv':
        return export_sales_report_csv_with_recommendations(request, start_date, end_date)
    
    # Filter sales by date range and business context
    sales = Sale.objects.business_specific().filter(sale_date__date__gte=start_date, sale_date__date__lte=end_date)
    
    # Calculate total sales and orders
    total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    total_orders = sales.count()
    
    # Get top selling products
    top_products = SaleItem.objects.business_specific().filter(
        sale__sale_date__date__gte=start_date,
        sale__sale_date__date__lte=end_date
    ).values('product__name').annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_sold')[:10]
    
    # Prepare data for sales trend chart
    sales_trend_data = sales.extra({'date': 'date(sale_date)'}).values('date').annotate(
        total=Sum('total_amount')
    ).order_by('date')
    
    # Fix: Handle the case where item['date'] might already be a string
    sales_trend_dates = []
    sales_trend_amounts = []
    
    for item in sales_trend_data:
        if isinstance(item['date'], str):
            # Already a string, use as is
            sales_trend_dates.append(item['date'])
        else:
            # Convert date object to string
            sales_trend_dates.append(item['date'].strftime('%Y-%m-%d'))
        sales_trend_amounts.append(float(item['total']))
    
    # Prepare data for top products chart
    product_names = [item['product__name'] for item in top_products]
    product_quantities = [float(item['total_sold']) for item in top_products]
    product_revenues = [float(item['total_revenue']) for item in top_products]
    
    # Convert to JSON for JavaScript
    sales_trend_dates_json = json.dumps(sales_trend_dates)
    sales_trend_amounts_json = json.dumps(sales_trend_amounts)
    product_names_json = json.dumps(product_names)
    product_quantities_json = json.dumps(product_quantities)
    product_revenues_json = json.dumps(product_revenues)
    
    # Get business settings
    from settings.models import BusinessSettings
    business_settings, created = BusinessSettings.objects.get_or_create(id=1)
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': float(total_sales),
        'total_orders': total_orders,
        'top_products': top_products,
        'sales_trend_dates_json': sales_trend_dates_json,
        'sales_trend_amounts_json': sales_trend_amounts_json,
        'product_names_json': product_names_json,
        'product_quantities_json': product_quantities_json,
        'product_revenues_json': product_revenues_json,
        'business_settings': business_settings,
    }
    
    return render(request, 'reports/sales.html', context)

def export_sales_report_csv_with_recommendations(request, start_date, end_date):
    """Export sales report data to CSV with recommendations"""
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow(['Sales Report', f'From {start_date} to {end_date}'])
    writer.writerow([])
    
    # Get sales data
    sales = Sale.objects.business_specific().filter(sale_date__date__gte=start_date, sale_date__date__lte=end_date)
    total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    total_orders = sales.count()
    
    # Get top selling products
    top_products = SaleItem.objects.business_specific().filter(
        sale__sale_date__date__gte=start_date,
        sale__sale_date__date__lte=end_date
    ).values('product__name').annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_sold')[:10]
    
    # Write summary data
    writer.writerow(['Summary'])
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total Sales', f'${float(total_sales):.2f}'])
    writer.writerow(['Total Orders', total_orders])
    if total_orders > 0:
        writer.writerow(['Average Order Value', f'${float(total_sales)/total_orders:.2f}'])
    writer.writerow([])
    
    # Write sales trend data
    sales_trend_data = sales.extra({'date': 'date(sale_date)'}).values('date').annotate(
        total=Sum('total_amount')
    ).order_by('date')
    
    writer.writerow(['Sales Trend'])
    writer.writerow(['Date', 'Sales Amount'])
    for item in sales_trend_data:
        date_str = item['date'].strftime('%Y-%m-%d') if hasattr(item['date'], 'strftime') else str(item['date'])
        writer.writerow([date_str, f"${float(item['total']):.2f}"])
    writer.writerow([])
    
    # Write top selling products
    writer.writerow(['Top Selling Products'])
    writer.writerow(['Product', 'Quantity Sold', 'Revenue'])
    for product in top_products:
        writer.writerow([
            product['product__name'], 
            product['total_sold'], 
            f"${float(product['total_revenue']):.2f}"
        ])
    writer.writerow([])
    
    # Generate and write recommendations
    recommendations = generate_sales_recommendations(float(total_sales), total_orders, top_products)
    
    writer.writerow(['Business Recommendations'])
    writer.writerow(['Priority', 'Category', 'Title', 'Description', 'Suggested Action'])
    for rec in recommendations:
        priority = rec.get('priority', 'medium')
        priority_label = {
            'high': 'HIGH',
            'medium': 'MEDIUM',
            'low': 'LOW',
            'positive': 'POSITIVE'
        }.get(priority, 'MEDIUM')
        
        writer.writerow([
            priority_label,
            rec.get('type', 'general').title(),
            rec.get('title', ''),
            rec.get('description', ''),
            rec.get('action', '')
        ])
    
    return response

def generate_sales_recommendations(total_sales, total_orders, top_products):
    """Generate sales-specific recommendations"""
    recommendations = []
    
    # Sales volume recommendations
    if total_orders < 10:
        recommendations.append({
            'type': 'sales_volume',
            'priority': 'high',
            'title': 'Low Sales Volume',
            'description': f'Only {total_orders} orders recorded in this period. This may indicate low customer traffic or sales opportunities.',
            'action': 'Implement promotional campaigns and review marketing strategies to increase customer acquisition.'
        })
    elif total_orders > 100:
        recommendations.append({
            'type': 'sales_volume',
            'priority': 'positive',
            'title': 'High Sales Volume',
            'description': f'Excellent sales volume with {total_orders} orders. This indicates strong market demand.',
            'action': 'Ensure inventory levels can sustain this demand and consider scaling operations.'
        })
    
    # Average order value recommendations
    if total_orders > 0:
        avg_order_value = total_sales / total_orders
        if avg_order_value < 25:
            recommendations.append({
                'type': 'sales_value',
                'priority': 'medium',
                'title': 'Low Average Order Value',
                'description': f'Average order value is ${avg_order_value:.2f}. There may be opportunities to increase this.',
                'action': 'Implement upselling and cross-selling techniques. Create product bundles or loyalty programs.'
            })
    
    # Product concentration recommendations
    if top_products:
        top_product = top_products[0] if top_products else None
        if top_product and top_product['total_sold'] > sum(p['total_sold'] for p in top_products) * 0.5:
            recommendations.append({
                'type': 'product_diversity',
                'priority': 'medium',
                'title': 'Product Concentration Risk',
                'description': f'Top product {top_product["product__name"]} represents over 50% of sales volume.',
                'action': 'Diversify product offerings to reduce dependency on single products and spread risk.'
            })
    
    return recommendations

@login_required
def inventory_report(request):
    # Check if export is requested
    if 'export' in request.GET and request.GET['export'] == 'csv':
        return export_inventory_report_csv(request)
    
    # Get low stock products (below reorder level)
    low_stock_products = Product.objects.business_specific().filter(
        quantity__lte=F('reorder_level'),
        is_active=True
    ).order_by('quantity')
    
    # Get out of stock products
    out_of_stock_products = Product.objects.business_specific().filter(
        quantity=0,
        is_active=True
    ).order_by('name')
    
    # Get expired products
    today = timezone.now().date()
    expired_products = Product.objects.business_specific().filter(
        expiry_date__lt=today,
        is_active=True
    ).order_by('expiry_date')
    
    # Get near expiry products (within 30 days)
    near_expiry_date = today + timedelta(days=30)
    near_expiry_products = Product.objects.business_specific().filter(
        expiry_date__gte=today,
        expiry_date__lte=near_expiry_date,
        is_active=True
    ).order_by('expiry_date')
    
    # Prepare data for stock level chart (top 10 products by quantity)
    stock_data = Product.objects.business_specific().filter(is_active=True).order_by('-quantity')[:10]
    stock_product_names = [product.name for product in stock_data]
    stock_product_quantities = [float(product.quantity) for product in stock_data]
    
    # Prepare data for product performance chart (top 10 products by sales in last 30 days)
    performance_start_date = today - timedelta(days=30)
    performance_data = SaleItem.objects.business_specific().filter(
        sale__sale_date__gte=performance_start_date
    ).values('product__name').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:10]
    
    performance_product_names = [item['product__name'] for item in performance_data]
    performance_product_quantities = [float(item['total_sold']) for item in performance_data]
    
    # Convert to JSON for JavaScript
    stock_product_names_json = json.dumps(stock_product_names)
    stock_product_quantities_json = json.dumps(stock_product_quantities)
    performance_product_names_json = json.dumps(performance_product_names)
    performance_product_quantities_json = json.dumps(performance_product_quantities)
    
    # Get business settings
    from settings.models import BusinessSettings
    business_settings, created = BusinessSettings.objects.get_or_create(id=1)
    
    context = {
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'expired_products': expired_products,
        'near_expiry_products': near_expiry_products,
        'today': today,
        'stock_product_names_json': stock_product_names_json,
        'stock_product_quantities_json': stock_product_quantities_json,
        'performance_product_names_json': performance_product_names_json,
        'performance_product_quantities_json': performance_product_quantities_json,
        'business_settings': business_settings,
    }
    
    return render(request, 'reports/inventory.html', context)

def export_inventory_report_csv(request):
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow(['Inventory Report'])
    writer.writerow([])
    
    # Write low stock products
    writer.writerow(['Low Stock Products (Below Reorder Level)'])
    writer.writerow(['Product', 'SKU', 'Current Stock', 'Reorder Level', 'Category'])
    
    low_stock_products = Product.objects.business_specific().filter(
        quantity__lte=F('reorder_level'),
        is_active=True
    ).select_related('category')
    
    for product in low_stock_products:
        writer.writerow([
            product.name,
            product.sku,
            product.quantity,
            product.reorder_level,
            product.category.name if product.category else ''
        ])
    
    writer.writerow([])
    
    # Write out of stock products
    writer.writerow(['Out of Stock Products'])
    writer.writerow(['Product', 'SKU', 'Category'])
    
    out_of_stock_products = Product.objects.business_specific().filter(
        quantity=0,
        is_active=True
    ).select_related('category')
    
    for product in out_of_stock_products:
        writer.writerow([
            product.name,
            product.sku,
            product.category.name if product.category else ''
        ])
    
    writer.writerow([])
    
    # Write expired products
    writer.writerow(['Expired Products'])
    writer.writerow(['Product', 'SKU', 'Expiry Date', 'Current Stock', 'Category'])
    
    today = timezone.now().date()
    expired_products = Product.objects.business_specific().filter(
        expiry_date__lt=today,
        is_active=True
    ).select_related('category')
    
    for product in expired_products:
        writer.writerow([
            product.name,
            product.sku,
            product.expiry_date,
            product.quantity,
            product.category.name if product.category else ''
        ])
    
    return response

@login_required
def profit_loss_report(request):
    # Get date range from request or use defaults
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if 'start_date' in request.GET and request.GET['start_date']:
        start_date = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
    if 'end_date' in request.GET and request.GET['end_date']:
        end_date = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
    
    # Check if export is requested
    if 'export' in request.GET and request.GET['export'] == 'csv':
        return export_profit_loss_report_csv_with_recommendations(request, start_date, end_date)
    
    # Calculate sales revenue
    sales = Sale.objects.business_specific().filter(sale_date__date__gte=start_date, sale_date__date__lte=end_date)
    sales_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # Calculate cost of goods sold (COGS)
    sale_items = SaleItem.objects.business_specific().filter(
        sale__sale_date__date__gte=start_date,
        sale__sale_date__date__lte=end_date
    )
    
    cogs = Decimal('0')
    for item in sale_items:
        cogs += Decimal(str(item.product.cost_price)) * Decimal(str(item.quantity))
    
    # Calculate expenses
    expenses = Expense.objects.business_specific().filter(date__gte=start_date, date__lte=end_date)
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Calculate profit metrics
    gross_profit = sales_revenue - cogs
    net_profit = gross_profit - total_expenses
    
    # Calculate profit margins
    gross_profit_margin = (float(gross_profit) / float(sales_revenue) * 100) if float(sales_revenue) > 0 else 0
    net_profit_margin = (float(net_profit) / float(sales_revenue) * 100) if float(sales_revenue) > 0 else 0
    
    # Prepare data for profit trend chart
    profit_trend_data = sales.extra({'date': 'date(sale_date)'}).values('date').annotate(
        total=Sum('total_amount')
    ).order_by('date')
    
    # Fix: Handle the case where item['date'] might already be a string
    profit_dates = []
    profit_amounts = []
    
    for item in profit_trend_data:
        if isinstance(item['date'], str):
            # Already a string, use as is
            profit_dates.append(item['date'])
        else:
            # Convert date object to string
            profit_dates.append(item['date'].strftime('%Y-%m-%d'))
        # Calculate daily profit (simplified)
        daily_sales = Sale.objects.business_specific().filter(sale_date__date=item['date'])
        daily_revenue = daily_sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        daily_items = SaleItem.objects.business_specific().filter(sale__sale_date__date=item['date'])
        # Fix: Use Decimal for daily COGS calculation
        daily_cogs = Decimal('0')
        for daily_item in daily_items:
            daily_cogs += Decimal(str(daily_item.product.cost_price)) * Decimal(str(daily_item.quantity))
        
        daily_profit = daily_revenue - daily_cogs
        profit_amounts.append(float(daily_profit))
    
    # Monthly profit summary
    monthly_profit_summary = []
    current_month = start_date.replace(day=1)
    
    while current_month <= end_date:
        # Get last day of month
        if current_month.month == 12:
            next_month = current_month.replace(year=current_month.year + 1, month=1, day=1)
        else:
            next_month = current_month.replace(month=current_month.month + 1, day=1)
        
        month_end = next_month - timedelta(days=1)
        
        # Calculate monthly data
        monthly_sales = Sale.objects.business_specific().filter(
            sale_date__date__gte=current_month,
            sale_date__date__lte=month_end
        )
        monthly_revenue = monthly_sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        monthly_items = SaleItem.objects.business_specific().filter(
            sale__sale_date__date__gte=current_month,
            sale__sale_date__date__lte=month_end
        )
        # Fix: Use Decimal for monthly COGS calculation
        monthly_cogs = Decimal('0')
        for monthly_item in monthly_items:
            monthly_cogs += Decimal(str(monthly_item.product.cost_price)) * Decimal(str(monthly_item.quantity))
        
        monthly_profit = monthly_revenue - monthly_cogs
        
        monthly_profit_summary.append({
            'month': current_month.strftime('%B %Y'),
            'revenue': float(monthly_revenue),
            'cogs': float(monthly_cogs),
            'profit': float(monthly_profit)
        })
        
        # Move to next month
        if current_month.month == 12:
            current_month = current_month.replace(year=current_month.year + 1, month=1, day=1)
        else:
            current_month = current_month.replace(month=current_month.month + 1, day=1)
    
    # Convert to JSON for JavaScript
    profit_dates_json = json.dumps(profit_dates)
    profit_amounts_json = json.dumps(profit_amounts)
    
    # Get business settings
    from settings.models import BusinessSettings
    business_settings, created = BusinessSettings.objects.get_or_create(id=1)
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'sales_revenue': float(sales_revenue),
        'cogs': float(cogs),
        'total_expenses': float(total_expenses),
        'gross_profit': float(gross_profit),
        'net_profit': float(net_profit),
        'gross_profit_margin': gross_profit_margin,
        'net_profit_margin': net_profit_margin,
        'profit_dates_json': profit_dates_json,
        'profit_amounts_json': profit_amounts_json,
        'monthly_profit_summary': monthly_profit_summary,
        'business_settings': business_settings,
    }
    
    return render(request, 'reports/profit_loss.html', context)

def export_profit_loss_report_csv_with_recommendations(request, start_date, end_date):
    """Export profit & loss report data to CSV with recommendations"""
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="profit_loss_report_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow(['Profit & Loss Report', f'From {start_date} to {end_date}'])
    writer.writerow([])
    
    # Calculate sales revenue
    sales = Sale.objects.business_specific().filter(sale_date__date__gte=start_date, sale_date__date__lte=end_date)
    sales_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # Calculate cost of goods sold (COGS)
    sale_items = SaleItem.objects.business_specific().filter(
        sale__sale_date__date__gte=start_date,
        sale__sale_date__date__lte=end_date
    )
    
    cogs = Decimal('0')
    for item in sale_items:
        cogs += Decimal(str(item.product.cost_price)) * Decimal(str(item.quantity))
    
    # Calculate expenses
    expenses = Expense.objects.business_specific().filter(date__gte=start_date, date__lte=end_date)
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Calculate profit metrics
    gross_profit = sales_revenue - cogs
    net_profit = gross_profit - total_expenses
    
    # Calculate profit margins
    gross_profit_margin = (float(gross_profit) / float(sales_revenue) * 100) if float(sales_revenue) > 0 else 0
    net_profit_margin = (float(net_profit) / float(sales_revenue) * 100) if float(sales_revenue) > 0 else 0
    
    # Write summary data
    writer.writerow(['Financial Summary'])
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Sales Revenue', f'${float(sales_revenue):.2f}'])
    writer.writerow(['Cost of Goods Sold (COGS)', f'${float(cogs):.2f}'])
    writer.writerow(['Gross Profit', f'${float(gross_profit):.2f}'])
    writer.writerow(['Gross Profit Margin', f'{gross_profit_margin:.2f}%'])
    writer.writerow(['Operating Expenses', f'${float(total_expenses):.2f}'])
    writer.writerow(['Net Profit', f'${float(net_profit):.2f}'])
    writer.writerow(['Net Profit Margin', f'{net_profit_margin:.2f}%'])
    writer.writerow([])
    
    # Write monthly profit summary
    monthly_profit_summary = []
    current_month = start_date.replace(day=1)
    
    writer.writerow(['Monthly Profit Summary'])
    writer.writerow(['Month', 'Revenue', 'COGS', 'Gross Profit', 'Expenses', 'Net Profit'])
    
    while current_month <= end_date:
        # Get last day of month
        if current_month.month == 12:
            next_month = current_month.replace(year=current_month.year + 1, month=1, day=1)
        else:
            next_month = current_month.replace(month=current_month.month + 1, day=1)
        
        month_end = next_month - timedelta(days=1)
        
        # Calculate monthly data
        monthly_sales = Sale.objects.business_specific().filter(
            sale_date__date__gte=current_month,
            sale_date__date__lte=month_end
        )
        monthly_revenue = monthly_sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        monthly_items = SaleItem.objects.business_specific().filter(
            sale__sale_date__date__gte=current_month,
            sale__sale_date__date__lte=month_end
        )
        monthly_cogs = Decimal('0')
        for monthly_item in monthly_items:
            monthly_cogs += Decimal(str(monthly_item.product.cost_price)) * Decimal(str(monthly_item.quantity))
        
        monthly_expenses = Expense.objects.business_specific().filter(
            date__gte=current_month,
            date__lte=month_end
        )
        monthly_expense_total = monthly_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        monthly_profit = monthly_revenue - monthly_cogs - monthly_expense_total
        
        writer.writerow([
            current_month.strftime('%B %Y'),
            f'${float(monthly_revenue):.2f}',
            f'${float(monthly_cogs):.2f}',
            f'${float(monthly_revenue - monthly_cogs):.2f}',
            f'${float(monthly_expense_total):.2f}',
            f'${float(monthly_profit):.2f}'
        ])
        
        # Move to next month
        if current_month.month == 12:
            current_month = current_month.replace(year=current_month.year + 1, month=1, day=1)
        else:
            current_month = current_month.replace(month=current_month.month + 1, day=1)
    
    writer.writerow([])
    
    # Generate and write recommendations
    recommendations = generate_profit_loss_recommendations(
        float(sales_revenue), float(cogs), float(total_expenses), 
        float(gross_profit), float(net_profit), gross_profit_margin, net_profit_margin
    )
    
    writer.writerow(['Business Recommendations'])
    writer.writerow(['Priority', 'Category', 'Title', 'Description', 'Suggested Action'])
    for rec in recommendations:
        priority = rec.get('priority', 'medium')
        priority_label = {
            'high': 'HIGH',
            'medium': 'MEDIUM',
            'low': 'LOW',
            'positive': 'POSITIVE'
        }.get(priority, 'MEDIUM')
        
        writer.writerow([
            priority_label,
            rec.get('type', 'general').title(),
            rec.get('title', ''),
            rec.get('description', ''),
            rec.get('action', '')
        ])
    
    return response

def generate_profit_loss_recommendations(sales_revenue, cogs, total_expenses, gross_profit, net_profit, gross_margin, net_margin):
    """Generate profit & loss specific recommendations"""
    recommendations = []
    
    # Profitability recommendations
    if net_margin < 5:
        recommendations.append({
            'type': 'profitability',
            'priority': 'high',
            'title': 'Low Profitability',
            'description': f'Net profit margin is {net_margin:.1f}%, which is below industry standards.',
            'action': 'Review pricing strategy, reduce operating costs, and optimize product mix.'
        })
    elif net_margin > 15:
        recommendations.append({
            'type': 'profitability',
            'priority': 'positive',
            'title': 'Strong Profitability',
            'description': f'Excellent net profit margin of {net_margin:.1f}%. This indicates strong financial performance.',
            'action': 'Reinvest profits strategically to sustain growth while maintaining this level of profitability.'
        })
    
    # Cost structure recommendations
    if sales_revenue > 0:
        cogs_ratio = (cogs / sales_revenue) * 100
        expense_ratio = (total_expenses / sales_revenue) * 100
        
        if cogs_ratio > 60:
            recommendations.append({
                'type': 'cost_management',
                'priority': 'medium',
                'title': 'High COGS Ratio',
                'description': f'Cost of goods sold represents {cogs_ratio:.1f}% of sales. This may impact profitability.',
                'action': 'Negotiate better supplier rates, review inventory management, and consider alternative suppliers.'
            })
        
        if expense_ratio > 25:
            recommendations.append({
                'type': 'cost_management',
                'priority': 'high',
                'title': 'High Operating Expenses',
                'description': f'Operating expenses account for {expense_ratio:.1f}% of sales. This is relatively high.',
                'action': 'Review discretionary spending, consolidate services, and optimize operational efficiency.'
            })
    
    # Break-even analysis
    if sales_revenue > 0 and total_expenses > 0:
        # Simplified break-even calculation
        bep = total_expenses / (gross_profit / sales_revenue) if gross_profit > 0 else 0
        if bep > sales_revenue * 1.2:
            recommendations.append({
                'type': 'financial_health',
                'priority': 'high',
                'title': 'High Break-Even Point',
                'description': 'Current sales are close to the break-even point. Small changes could impact profitability.',
                'action': 'Increase sales volume, reduce fixed costs, or improve pricing strategy.'
            })
    
    return recommendations

@login_required
def expenses_report(request):
    # Get date range from request or use defaults
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if 'start_date' in request.GET and request.GET['start_date']:
        start_date = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
    if 'end_date' in request.GET and request.GET['end_date']:
        end_date = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
    
    # Check if export is requested
    if 'export' in request.GET and request.GET['export'] == 'csv':
        return export_expenses_report_csv_with_recommendations(request, start_date, end_date)
    
    # Filter expenses by date range
    expenses = Expense.objects.filter(date__gte=start_date, date__lte=end_date)
    
    # Calculate total expenses
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Group expenses by category with count
    expense_by_category = expenses.values('category__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Prepare data for expense trend chart
    expense_trend_data = expenses.extra({'date': 'date(date)'}).values('date').annotate(
        total=Sum('amount')
    ).order_by('date')
    
    # Fix: Handle the case where item['date'] might already be a string
    expense_dates = []
    expense_amounts = []
    
    for item in expense_trend_data:
        if isinstance(item['date'], str):
            # Already a string, use as is
            expense_dates.append(item['date'])
        else:
            # Convert date object to string
            expense_dates.append(item['date'].strftime('%Y-%m-%d'))
        expense_amounts.append(float(item['total']))
    
    # Prepare data for category chart
    category_names = [item['category__name'] for item in expense_by_category]
    category_amounts = [float(item['total']) for item in expense_by_category]
    
    # Convert to JSON for JavaScript
    expense_dates_json = json.dumps(expense_dates)
    expense_amounts_json = json.dumps(expense_amounts)
    category_names_json = json.dumps(category_names)
    category_amounts_json = json.dumps(category_amounts)
    
    # Get business settings
    from settings.models import BusinessSettings
    business_settings, created = BusinessSettings.objects.get_or_create(id=1)
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_expenses': float(total_expenses),
        'expense_by_category': expense_by_category,
        'expense_dates_json': expense_dates_json,
        'expense_amounts_json': expense_amounts_json,
        'category_names_json': category_names_json,
        'category_amounts_json': category_amounts_json,
        'business_settings': business_settings,
    }
    
    return render(request, 'reports/expenses.html', context)

def export_expenses_report_csv_with_recommendations(request, start_date, end_date):
    """Export expenses report data to CSV with recommendations"""
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="expenses_report_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow(['Expense Report', f'From {start_date} to {end_date}'])
    writer.writerow([])
    
    # Get expenses data
    expenses = Expense.objects.business_specific().filter(date__gte=start_date, date__lte=end_date)
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Group expenses by category
    expense_by_category = expenses.values('category__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Write summary data
    writer.writerow(['Summary'])
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total Expenses', f'${float(total_expenses):.2f}'])
    writer.writerow(['Number of Expense Entries', expenses.count()])
    writer.writerow([])
    
    # Write expenses by category
    writer.writerow(['Expenses by Category'])
    writer.writerow(['Category', 'Total Amount', 'Number of Expenses', 'Percentage of Total'])
    for category in expense_by_category:
        percentage = (float(category['total']) / float(total_expenses) * 100) if float(total_expenses) > 0 else 0
        writer.writerow([
            category['category__name'] or 'Uncategorized',
            f"${float(category['total']):.2f}",
            category['count'],
            f"{percentage:.1f}%"
        ])
    writer.writerow([])
    
    # Write detailed expenses
    writer.writerow(['Detailed Expenses'])
    writer.writerow(['Date', 'Category', 'Description', 'Amount'])
    
    detailed_expenses = expenses.order_by('-date')
    for expense in detailed_expenses:
        writer.writerow([
            expense.date.strftime('%Y-%m-%d') if expense.date else '',
            expense.category.name if expense.category else 'Uncategorized',
            expense.description,
            f"${float(expense.amount):.2f}"
        ])
    writer.writerow([])
    
    # Generate and write recommendations
    recommendations = generate_expense_recommendations(float(total_expenses), expense_by_category, expenses.count())
    
    writer.writerow(['Business Recommendations'])
    writer.writerow(['Priority', 'Category', 'Title', 'Description', 'Suggested Action'])
    for rec in recommendations:
        priority = rec.get('priority', 'medium')
        priority_label = {
            'high': 'HIGH',
            'medium': 'MEDIUM',
            'low': 'LOW',
            'positive': 'POSITIVE'
        }.get(priority, 'MEDIUM')
        
        writer.writerow([
            priority_label,
            rec.get('type', 'general').title(),
            rec.get('title', ''),
            rec.get('description', ''),
            rec.get('action', '')
        ])
    
    return response

def generate_expense_recommendations(total_expenses, expense_by_category, expense_count):
    """Generate expense-specific recommendations"""
    recommendations = []
    
    # Overall expense level recommendations
    if total_expenses > 10000:
        recommendations.append({
            'type': 'expense_level',
            'priority': 'high',
            'title': 'High Expense Level',
            'description': f'Total expenses of ${total_expenses:.2f} may be high for your business size.',
            'action': 'Review all expense categories and identify areas for cost reduction.'
        })
    elif total_expenses < 1000:
        recommendations.append({
            'type': 'expense_level',
            'priority': 'positive',
            'title': 'Efficient Expense Management',
            'description': f'Total expenses of ${total_expenses:.2f} appear to be well-controlled.',
            'action': 'Continue monitoring expenses to maintain this level of efficiency.'
        })
    
    # Category concentration recommendations
    if expense_by_category:
        top_category = expense_by_category[0] if expense_by_category else None
        if top_category and (float(top_category['total']) / total_expenses) > 0.4:
            recommendations.append({
                'type': 'expense_diversity',
                'priority': 'medium',
                'title': 'Expense Concentration Risk',
                'description': f'Top expense category ({top_category["category__name"]}) represents over 40% of total expenses.',
                'action': 'Diversify expenses across categories and review if this concentration is necessary.'
            })
    
    # Expense frequency recommendations
    if expense_count > 50:
        recommendations.append({
            'type': 'expense_frequency',
            'priority': 'medium',
            'title': 'High Expense Frequency',
            'description': f'{expense_count} expense entries recorded. This may indicate fragmented spending.',
            'action': 'Consolidate similar expenses and review approval processes for small purchases.'
        })
    
    return recommendations

# Test charts view
def test_charts(request):
    """Test view to verify chart background removal"""
    from settings.models import BusinessSettings
    business_settings, created = BusinessSettings.objects.get_or_create(id=1)
    
    return render(request, 'reports/test_charts.html', {
        'business_settings': business_settings,
    })