# Email Configuration Guide

This document explains how to configure email settings for the Inventory Management System.

## Overview

The system supports various email backends:
1. SMTP (Gmail, SendGrid, etc.)
2. Console (Development - Prints to terminal)
3. Amazon SES

## Types of Emails Sent

The system sends several types of emails:
1. Business Registration Confirmation - Sent when a new business registers
2. Business Approval/Rejection - Sent when a business is approved or rejected by superadmin
3. Account Suspension - Sent when a user account is suspended
4. Password Reset - Sent when a user requests to reset their password

## Setting Up Email Configuration

### Method 1: Using the Web Interface (Recommended)

1. Log in as a superadmin
2. Navigate to Superadmin Dashboard
3. Go to Email Settings section
4. Configure the following fields:
   - Email Backend: Select SMTP for production use
   - Email Host: SMTP server address (e.g., smtp.gmail.com for Gmail)
   - Email Port: SMTP port (587 for TLS, 465 for SSL)
   - Email Host User: Your email address or username
   - Email Host Password: Your password or app password (not your regular password!)
   - Use TLS: Check if using TLS encryption
   - Use SSL: Check if using SSL encryption
   - Default From Email: Sender email address

### Method 2: Using Django Management Commands

Run the following command to configure email settings:

```bash
python manage.py setup_email --host smtp.gmail.com --port 587 --username your-email@gmail.com --password your-app-password --from-email "Inventory System <your-email@gmail.com>" --use-tls
```

### Method 3: Direct Database Configuration

You can also configure email settings directly in the database using Django shell:

```bash
python manage.py shell
```

Then in the shell:

```python
from settings.models import EmailSettings
email_settings = EmailSettings.objects.get_or_create(id=1)[0]
email_settings.email_backend = "django.core.mail.backends.smtp.EmailBackend"
email_settings.email_host = "smtp.gmail.com"
email_settings.email_port = 587
email_settings.email_host_user = "your-email@gmail.com"
email_settings.email_host_password = "your-app-password"  # Use app password, not regular password
email_settings.email_use_tls = True
email_settings.email_use_ssl = False
email_settings.default_from_email = "Inventory System <your-email@gmail.com>"
email_settings.save()
```

## Testing Email Configuration

### Test General Email Functionality

To test if your email configuration is working:

```bash
python manage.py test_email --to recipient@example.com
```

### Test Business Registration Email

To specifically test the business registration email:

```bash
python manage.py test_business_email --to recipient@example.com --business-name "Test Business" --username "testuser"
```

## Common Email Providers Configuration

### Gmail

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
3. Configure settings:
   - Email Host: smtp.gmail.com
   - Email Port: 587
   - Email Host User: your-email@gmail.com
   - Email Host Password: your-app-password (NOT your regular Gmail password)
   - Use TLS: Checked
   - Use SSL: Unchecked

### SendGrid

1. Create a SendGrid account
2. Generate an API key
3. Configure settings:
   - Email Host: smtp.sendgrid.net
   - Email Port: 587
   - Email Host User: apikey
   - Email Host Password: your-sendgrid-api-key
   - Use TLS: Checked
   - Use SSL: Unchecked

### Amazon SES

1. Set up Amazon SES account
2. Verify your domain or email address
3. Create SMTP credentials
4. Configure settings:
   - Email Backend: django_ses.SESBackend
   - (Additional AWS configuration required)

## Troubleshooting

### No Emails Received

1. Check that email settings are correctly configured
2. Verify that the recipient email address is correct
3. Check spam/junk folders
4. Look at application logs for errors

### Error Messages

Common error messages and solutions:

- "Connection refused": Check email host and port settings
- "Authentication failed": Verify username and password/app password
  - For Gmail, make sure you're using an App Password, not your regular password
  - Ensure 2-Factor Authentication is enabled on your Google account
- "TLS/SSL error": Check TLS/SSL settings match your provider's requirements

### Gmail Specific Issues

If you're getting "Username and Password not accepted" errors with Gmail:

1. Make sure 2-Factor Authentication is enabled on your Google account
2. Generate an App Password specifically for this application:
   - Go to your Google Account settings
   - Navigate to Security → 2-Step Verification → App passwords
   - Select "Mail" and your device
   - Use the generated 16-character password in place of your regular password
3. Never use your regular Gmail password with SMTP - it won't work

### Debugging

Enable debug logging to see detailed email sending information:

1. Check the application logs
2. Run test email command with detailed output
3. Verify that the EmailSettingsMiddleware is enabled in settings.py

## Development Environment

For development, you can use the console email backend which prints emails to the terminal:

```bash
python manage.py setup_email --backend console
```

Or manually set:
1. Email Backend to "Console (Development - Print to Terminal)" in the web interface
2. Or set EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend" in settings

This is useful for testing without actually sending emails.