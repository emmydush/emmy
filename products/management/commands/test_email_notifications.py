from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from products.models import Product
from authentication.models import User


class Command(BaseCommand):
    help = "Test email notifications for low stock and expired products"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email", type=str, help="Email address to send test notifications to"
        )

    def handle(self, *args, **options):
        # Get email address
        email_address = options["email"]
        if not email_address:
            # Try to get admin user email
            admin_user = User.objects.filter(role="admin", is_active=True).first()
            if admin_user and admin_user.email:
                email_address = admin_user.email
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "No email address provided and no admin user with email found."
                    )
                )
                return

        # Test sending a simple email
        try:
            send_mail(
                "Test Email from Inventory Management System",
                "This is a test email to verify that email notifications are working correctly.",
                settings.DEFAULT_FROM_EMAIL,
                [email_address],
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Successfully sent test email to {email_address}")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send test email: {str(e)}"))
            return

        # Test sending a low stock notification email
        try:
            # Get some products for testing
            products = Product.objects.filter(is_active=True)[:3]

            context = {
                "business_name": "Test Business",
                "low_stock_products": products,
                "today": settings.TIME_ZONE,
            }

            # Render email content
            message = render_to_string("emails/low_stock_products.html", context)
            plain_message = render_to_string("emails/low_stock_products.txt", context)

            send_mail(
                "[Test] Low Stock Alert",
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email_address],
                html_message=message,
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully sent low stock test email to {email_address}"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to send low stock test email: {str(e)}")
            )
