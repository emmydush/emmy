from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.conf import settings


class Command(BaseCommand):
    help = "Test email configuration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            help="Email address to send test email to",
            required=False,
        )

    def handle(self, *args, **options):
        # Get email address
        email_address = options.get("email") or "emmychris915@gmail.com"

        try:
            # Create test email
            subject = "Test Email from Smart Business System"
            body = """
            <html>
            <body>
                <h2>Smart Business System - Email Test</h2>
                <p>This is a test email to verify that the email configuration is working correctly.</p>
                <p>If you received this email, the system can successfully send reports automatically.</p>
                <hr>
                <p><small>This is an automated message from Smart Business System</small></p>
            </body>
            </html>
            """

            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_address],
            )
            email.content_subtype = "html"

            # Send email
            email.send()

            self.stdout.write(
                self.style.SUCCESS(f"Test email successfully sent to {email_address}")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send test email: {str(e)}"))
