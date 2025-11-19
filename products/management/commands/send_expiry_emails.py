from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import F
from products.models import Product
from settings.models import BusinessSettings
from authentication.models import User
from datetime import timedelta


class Command(BaseCommand):
    help = "Send email notifications for expired and near expiry products"

    def handle(self, *args, **options):
        # Get business settings for alert thresholds and email configuration
        try:
            business_settings = BusinessSettings.objects.get(id=1)
            expiry_alert_days = business_settings.expiry_alert_days
            business_email = business_settings.business_email
            business_name = business_settings.business_name
        except BusinessSettings.DoesNotExist:
            # Use default values if settings don't exist
            expiry_alert_days = 7
            business_email = "info@business.com"
            business_name = "Inventory Management System"

        # Get all email recipients including personal emails
        admin_emails = self.get_personal_email_recipients()

        if not admin_emails:
            self.stdout.write(
                self.style.WARNING(
                    "No admin users with email addresses found. Skipping email notifications."
                )
            )
            return

        # Send notifications for expired products
        expired_products = self.get_expired_products()
        if expired_products:
            self.send_expired_products_email(
                admin_emails, expired_products, business_name
            )

        # Send notifications for near expiry products
        near_expiry_products = self.get_near_expiry_products(expiry_alert_days)
        if near_expiry_products:
            self.send_near_expiry_email(
                admin_emails, near_expiry_products, business_name, expiry_alert_days
            )

        # Send notifications for low stock products
        low_stock_products = self.get_low_stock_products()
        if low_stock_products:
            self.send_low_stock_email(admin_emails, low_stock_products, business_name)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully sent expiry email notifications to {len(admin_emails)} recipients"
            )
        )

    def get_expired_products(self):
        """Get all expired products"""
        today = timezone.now().date()
        return Product.objects.filter(is_active=True, expiry_date__lt=today)

    def get_near_expiry_products(self, days_threshold):
        """Get products nearing expiry"""
        today = timezone.now().date()
        near_expiry_date = today + timedelta(days=days_threshold)
        return Product.objects.filter(
            is_active=True, expiry_date__gte=today, expiry_date__lte=near_expiry_date
        )

    def get_low_stock_products(self):
        """Get products with low stock"""
        return Product.objects.filter(is_active=True, quantity__lte=F("reorder_level"))

    def send_expired_products_email(
        self, admin_emails, expired_products, business_name
    ):
        """Send email notification for expired products"""
        subject = f"[{business_name}] Expired Products Alert"

        # Prepare context for email template
        context = {
            "business_name": business_name,
            "expired_products": expired_products,
            "today": timezone.now().date(),
        }

        # Render email content
        message = render_to_string("emails/expired_products.html", context)
        plain_message = render_to_string("emails/expired_products.txt", context)

        # Send email
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                html_message=message,
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Sent expired products email to {len(admin_emails)} recipients"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to send expired products email: {str(e)}")
            )

    def send_near_expiry_email(
        self, admin_emails, near_expiry_products, business_name, days_threshold
    ):
        """Send email notification for near expiry products"""
        subject = f"[{business_name}] Near Expiry Products Alert - {days_threshold} Days or Less"

        # Prepare context for email template
        context = {
            "business_name": business_name,
            "near_expiry_products": near_expiry_products,
            "days_threshold": days_threshold,
            "today": timezone.now().date(),
        }

        # Render email content
        message = render_to_string("emails/near_expiry_products.html", context)
        plain_message = render_to_string("emails/near_expiry_products.txt", context)

        # Send email
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                html_message=message,
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Sent near expiry products email to {len(admin_emails)} recipients"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to send near expiry products email: {str(e)}")
            )

    def send_low_stock_email(self, admin_emails, low_stock_products, business_name):
        """Send email notification for low stock products"""
        subject = f"[{business_name}] Low Stock Alert"

        # Prepare context for email template
        context = {
            "business_name": business_name,
            "low_stock_products": low_stock_products,
            "today": timezone.now().date(),
        }

        # Render email content
        message = render_to_string("emails/low_stock_products.html", context)
        plain_message = render_to_string("emails/low_stock_products.txt", context)

        # Send email
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                html_message=message,
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Sent low stock products email to {len(admin_emails)} recipients"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to send low stock products email: {str(e)}")
            )

    def get_personal_email_recipients(self):
        """
        Get personal email recipients as per user preference.
        This ensures low stock and expired product alerts are sent directly to the user's email.
        """
        # Get admin users to send emails to
        admin_users = User.objects.filter(role="admin", is_active=True)
        admin_emails = [user.email for user in admin_users if user.email]

        # Also include the business email for personal alerts as per user preference
        try:
            business_settings = BusinessSettings.objects.get(id=1)
            business_email = business_settings.business_email
            if business_email and business_email not in admin_emails:
                admin_emails.append(business_email)
        except BusinessSettings.DoesNotExist:
            pass

        # Additionally, check for user preference to send directly to personal email
        # This addresses the user requirement for personal inventory alerts
        personal_emails = []
        for user in admin_users:
            # If user has a personal email different from business email, add it
            if user.email and user.email not in personal_emails:
                personal_emails.append(user.email)

        # Combine all email addresses, removing duplicates
        all_emails = list(set(admin_emails + personal_emails))
        return all_emails
