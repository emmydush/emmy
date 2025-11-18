# Real-Time Stock Levels Monitoring System

This feature provides real-time monitoring of stock levels with instant alerts to prevent stock theft and identify abnormal patterns.

## Features

### 1. Abnormal Stock Reduction Detection
- Automatically detects when products are reducing at an abnormal rate
- Compares current sales to historical averages
- Generates alerts when sales exceed 3x the average daily sales

### 2. Low Stock Alerts
- Monitors products that fall below their reorder level
- Provides clear warnings about possible missing items
- Categorizes alerts by severity (low, medium, high, critical)

### 3. Real-Time Notifications
- Instant alerts when stock issues are detected
- Clear, actionable messages that identify the problem
- Integration with existing notification system

## Alert Types

### Abnormal Reduction Alerts
```
⚠️ Product X reducing abnormally. Today's sales: 50, Average daily sales: 10
```

### Low Stock Alerts
```
⚠️ Low stock – possible missing items for Product X. Current stock: 5 units
```

## Implementation Details

### Models
- `StockAlert`: Stores all stock-related alerts
- `StockMovement`: Tracks all stock movements for analysis

### Monitoring Functions
- `check_abnormal_reduction()`: Detects abnormal sales patterns
- `check_low_stock_alerts()`: Identifies products below reorder level
- `check_expired_products()`: Finds expired products

### Signals
- Automatically tracks stock movements when:
  - Sales are created
  - Purchase items are received
  - Stock adjustments are approved
  - Sale items are deleted

### Scheduled Tasks
The system runs checks automatically:
- Every hour during business hours (9 AM to 6 PM)

## Setup

### Prerequisites
- Django 5.1+
- Python 3.8+

### Installation
1. Add `products` to your `INSTALLED_APPS`
2. Run migrations:
   ```bash
   python manage.py migrate
   ```
3. Set up scheduled tasks (see SCHEDULED_TASKS.md)

### Configuration
No additional configuration is required. The system uses existing product and business models.

## Usage

### Manual Testing
```bash
python manage.py check_stock_alerts
```

### Automatic Monitoring
The system automatically monitors stock levels and generates alerts based on:
- Historical sales data
- Reorder levels
- Real-time stock movements

## Customization

### Alert Thresholds
- Abnormal reduction threshold: 3x average daily sales
- Low stock threshold: Product's reorder_level field

### Alert Messages
Alert messages can be customized in the `stock_monitoring.py` file.

## Testing

Run the stock alert tests:
```bash
python manage.py test products.tests.StockAlertTestCase
```

## Troubleshooting

### No Alerts Generated
1. Check that products have sales data
2. Verify that reorder levels are set correctly
3. Ensure scheduled tasks are running

### False Positives
- Adjust the abnormal reduction threshold in `stock_monitoring.py`
- Review product categorization and sales patterns

## Security

The system follows the existing multi-tenancy model and only shows alerts to users within the same business.