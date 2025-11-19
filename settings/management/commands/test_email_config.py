from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from settings.models import EmailSettings


class Command(BaseCommand):
    help = "Test the current email configuration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--recipient", type=str, help="Email address to send test email to"
        )

    def handle(self, *args, **options):
        # Get email settings
        try:
            email_settings = EmailSettings.objects.get(id=1)
        except EmailSettings.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    "Email settings not configured. Please configure email settings first."
                )
            )
            return

        # Get recipient email
        recipient_email = options["recipient"]
        if not recipient_email:
            # Try to get from business settings
            try:
                from settings.models import BusinessSettings

                business_settings = BusinessSettings.objects.get(id=1)
                recipient_email = business_settings.business_email
            except:
                self.stdout.write(
                    self.style.ERROR(
                        "No recipient email provided and no business email configured."
                    )
                )
                return

        # Test sending email
        try:
            send_mail(
                "Test Email from Inventory Management System",
                "This is a test email to verify that your email configuration is working correctly.",
                email_settings.default_from_email,
                [recipient_email],
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Successfully sent test email to {recipient_email}")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send test email: {str(e)}"))
