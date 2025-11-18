from django.utils import timezone
from django.db.models import Avg, Count, Q, F
from .models import Product, StockAlert, StockMovement
from superadmin.middleware import get_current_business
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

def create_stock_alert(product, alert_type, severity, message, current_stock, previous_stock=None, threshold=None):
    """Create a stock alert for a product"""
    try:
        business = get_current_business()
        if not business:
            logger.warning("No business context found when creating stock alert")
            return None
            
        alert = StockAlert.objects.create(
            business=business,
            product=product,
            alert_type=alert_type,
            severity=severity,
            message=message,
            current_stock=current_stock,
            previous_stock=previous_stock,
            threshold=threshold
        )
        logger.info(f"Created stock alert: {alert}")
        return alert
    except Exception as e:
        logger.error(f"Error creating stock alert: {e}")
        return None

def track_stock_movement(product, movement_type, quantity, previous_quantity, new_quantity, 
                        reference_id=None, reference_model=None, created_by=None):
    """Track a stock movement for pattern analysis"""
    try:
        business = get_current_business()
        if not business:
            logger.warning("No business context found when tracking stock movement")
            return None
            
        movement = StockMovement.objects.create(
            business=business,
            product=product,
            movement_type=movement_type,
            quantity=quantity,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            reference_id=reference_id,
            reference_model=reference_model,
            created_by=created_by
        )
        logger.info(f"Tracked stock movement: {movement}")
        return movement
    except Exception as e:
        logger.error(f"Error tracking stock movement: {e}")
        return None

def check_low_stock_alerts():
    """Check for low stock products and create alerts"""
    try:
        business = get_current_business()
        if not business:
            logger.warning("No business context found when checking low stock alerts")
            return
            
        # Get all active products with low stock
        low_stock_products = Product.objects.business_specific().filter(
            is_active=True,
            quantity__lte=F('reorder_level')
        )
        
        for product in low_stock_products:
            # Check if an alert already exists for this product
            existing_alert = StockAlert.objects.filter(
                business=business,
                product=product,
                alert_type='low_stock',
                is_resolved=False
            ).first()
            
            if not existing_alert:
                # Create a new low stock alert with the specific message format requested
                message = f"⚠️ Low stock – possible missing items for {product.name}. Current stock: {product.quantity} {product.unit.symbol if product.unit else ''}"
                severity = 'high' if product.quantity <= product.reorder_level / 2 else 'medium'
                
                create_stock_alert(
                    product=product,
                    alert_type='low_stock',
                    severity=severity,
                    message=message,
                    current_stock=product.quantity,
                    threshold=product.reorder_level
                )
    except Exception as e:
        logger.error(f"Error checking low stock alerts: {e}")

def check_abnormal_reduction():
    """Check for abnormal stock reductions"""
    try:
        business = get_current_business()
        if not business:
            logger.warning("No business context found when checking abnormal reductions")
            return
            
        # Get products with recent movements (last 24 hours)
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        recent_movements = StockMovement.objects.filter(
            business=business,
            created_at__gte=twenty_four_hours_ago,
            movement_type='sale'
        ).select_related('product')
        
        # Group movements by product
        product_movements = {}
        for movement in recent_movements:
            if movement.product.id not in product_movements:
                product_movements[movement.product.id] = {
                    'product': movement.product,
                    'movements': []
                }
            product_movements[movement.product.id]['movements'].append(movement)
        
        # Check each product for abnormal patterns
        for product_data in product_movements.values():
            product = product_data['product']
            movements = product_data['movements']
            
            # Calculate average daily sales for this product over the last week
            one_week_ago = timezone.now() - timedelta(days=7)
            weekly_movements = StockMovement.objects.filter(
                business=business,
                product=product,
                movement_type='sale',
                created_at__gte=one_week_ago
            )
            
            if weekly_movements.count() > 0:
                avg_daily_sales = weekly_movements.aggregate(
                    avg_quantity=Avg('quantity')
                )['avg_quantity']
                
                # Calculate today's sales
                today_sales = sum([movement.quantity for movement in movements])
                
                # Check if today's sales are significantly higher than average
                if avg_daily_sales and today_sales > avg_daily_sales * 3:  # 3x average is abnormal
                    # Check if an alert already exists for this product
                    existing_alert = StockAlert.objects.filter(
                        business=business,
                        product=product,
                        alert_type='abnormal_reduction',
                        is_resolved=False
                    ).first()
                    
                    if not existing_alert:
                        # Create an abnormal reduction alert with the specific message format requested
                        message = f"⚠️ Product {product.name} reducing abnormally. Today's sales: {today_sales}, Average daily sales: {avg_daily_sales:.2f}"
                        create_stock_alert(
                            product=product,
                            alert_type='abnormal_reduction',
                            severity='high',
                            message=message,
                            current_stock=product.quantity,
                            previous_stock=product.quantity + today_sales
                        )
    except Exception as e:
        logger.error(f"Error checking abnormal reductions: {e}")

def check_expired_products():
    """Check for expired products and create alerts"""
    try:
        business = get_current_business()
        if not business:
            logger.warning("No business context found when checking expired products")
            return
            
        # Get products with expiry dates that have passed
        expired_products = Product.objects.business_specific().filter(
            is_active=True,
            expiry_date__lt=timezone.now().date()
        )
        
        for product in expired_products:
            # Check if an alert already exists for this product
            existing_alert = StockAlert.objects.filter(
                business=business,
                product=product,
                alert_type='expired',
                is_resolved=False
            ).first()
            
            if not existing_alert:
                # Create an expired product alert
                message = f"⚠️ Product {product.name} has expired. Expiry date: {product.expiry_date}"
                create_stock_alert(
                    product=product,
                    alert_type='expired',
                    severity='high',
                    message=message,
                    current_stock=product.quantity
                )
    except Exception as e:
        logger.error(f"Error checking expired products: {e}")

def resolve_alert(alert_id, resolved_by=None):
    """Mark an alert as resolved"""
    try:
        alert = StockAlert.objects.get(id=alert_id)
        alert.is_resolved = True
        alert.resolved_by = resolved_by
        alert.resolved_at = timezone.now()
        alert.save()
        logger.info(f"Resolved stock alert: {alert}")
        return alert
    except StockAlert.DoesNotExist:
        logger.warning(f"Stock alert with id {alert_id} not found")
        return None
    except Exception as e:
        logger.error(f"Error resolving stock alert: {e}")

# Import F at the top of the file
from django.db.models import F