# Scheduled Tasks Setup

This document explains how to set up scheduled tasks for automatic expiry date alerts and other background jobs.

## Available Management Commands

1. `generate_notifications` - Creates in-app notifications for low stock, expired, and near expiry products
2. `send_expiry_emails` - Sends email notifications for expired and near expiry products
3. `check_stock_alerts` - Checks for abnormal stock reductions and low stock situations

## Setting Up Scheduled Tasks

### Option 1: Using Cron (Linux/macOS)

Add the following lines to your crontab (`crontab -e`):

```bash
# Run notifications check every day at 9:00 AM
0 9 * * * cd /path/to/your/project && python manage.py generate_notifications

# Send expiry emails every day at 9:30 AM
30 9 * * * cd /path/to/your/project && python manage.py send_expiry_emails

# Check stock alerts every hour during business hours (9 AM to 6 PM)
0 9-18 * * * cd /path/to/your/project && python manage.py check_stock_alerts
```

### Option 2: Using Windows Task Scheduler

1. Open Task Scheduler
2. Create a new task
3. Set trigger to daily at your preferred time
4. Set action to run a program:
   - Program: `python`
   - Arguments: `manage.py generate_notifications`
   - Start in: `C:\path/to/your/project`

For stock alerts, create a separate task:
1. Open Task Scheduler
2. Create a new task
3. Set trigger to run every hour during business hours
4. Set action to run a program:
   - Program: `python`
   - Arguments: `manage.py check_stock_alerts`
   - Start in: `C:\path/to/your/project`

### Option 3: Using Celery (Advanced)

For more complex scheduling needs, you can set up Celery with Redis or RabbitMQ:

1. Install Celery and Redis:
   ```bash
   pip install celery redis
   ```

2. Configure Celery in your Django settings
3. Create Celery tasks for the management commands
4. Run Celery worker and beat services

## Configuring Email Settings

### For Development

The system is configured by default to use the console email backend, which prints emails to the terminal. This is useful for development and testing.

### For Gmail

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
3. Update your settings.py:
   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = 'smtp.gmail.com'
   EMAIL_PORT = 587
   EMAIL_USE_TLS = True
   EMAIL_HOST_USER = 'your-email@gmail.com'
   EMAIL_HOST_PASSWORD = 'your-app-password'
   DEFAULT_FROM_EMAIL = 'Inventory Management System <your-email@gmail.com>'
   ```

### For SendGrid

1. Create a SendGrid account
2. Generate an API key
3. Update your settings.py:
   ```python
   EMAIL_HOST = 'smtp.sendgrid.net'
   EMAIL_HOST_USER = 'apikey'
   EMAIL_HOST_PASSWORD = 'your-sendgrid-api-key'
   EMAIL_PORT = 587
   EMAIL_USE_TLS = True
   ```

### For Amazon SES

1. Set up an Amazon AWS account
2. Configure SES (Simple Email Service)
3. Get your access keys
4. Install the Django SES package:
   ```bash
   pip install django-ses
   ```
5. Update your settings.py:
   ```python
   EMAIL_BACKEND = 'django_ses.SESBackend'
   AWS_ACCESS_KEY_ID = 'your-access-key-id'
   AWS_SECRET_ACCESS_KEY = 'your-secret-access-key'
   AWS_SES_REGION_NAME = 'us-east-1'  # Change to your region
   AWS_SES_REGION_ENDPOINT = 'email.us-east-1.amazonaws.com'  # Change to your region endpoint
   ```

### For Other SMTP Providers

Update the EMAIL_HOST and EMAIL_PORT settings according to your email provider's SMTP settings:
- **Yahoo**: EMAIL_HOST = 'smtp.mail.yahoo.com', EMAIL_PORT = 587
- **Outlook/Hotmail**: EMAIL_HOST = 'smtp-mail.outlook.com', EMAIL_PORT = 587
- **Custom SMTP**: Use your provider's SMTP settings

## Configuring Alert Thresholds

You can configure the expiry alert thresholds in the Business Settings section of the application:

1. Go to Settings → Business Settings
2. Adjust "Expiry Alert Days" (urgent alerts) and "Near Expiry Alert Days" (early warnings)
3. Save the settings

Default values:
- Expiry Alert Days: 7 days (urgent alerts)
- Near Expiry Alert Days: 30 days (early warnings)

## Personal Inventory Alerts

As per user preference, low stock and expired product alerts are sent directly to the business email address configured in Business Settings, ensuring immediate personal notification regardless of system-wide notification settings.

## Testing the Setup

To test the scheduled tasks manually:

```bash
# Test notifications
python manage.py generate_notifications

# Test email alerts
python manage.py send_expiry_emails

# Test stock alerts
python manage.py check_stock_alerts
```

Check the console output for any errors or success messages.

For email testing in development, emails will be printed to the console. In production, they will be sent to the configured email addresses.