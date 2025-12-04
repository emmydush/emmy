from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from settings.models import EmailSettings
from settings.utils import apply_email_settings


class Command(BaseCommand):
    help = "Troubleshoot Gmail authentication issues"

    def add_arguments(self, parser):
        parser.add_argument(
            "--test-email",
            type=str,
            help="Test email address to send a test message to",
        )

    def handle(self, *args, **options):
        self.stdout.write("Troubleshooting Gmail authentication issues...")

        # Check if email settings exist
        try:
            email_settings = EmailSettings.objects.get(id=1)
        except EmailSettings.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    "No email settings found. Please configure email settings first."
                )
            )
            return

        # Display current settings (hide password for security)
        self.stdout.write("\nCurrent Email Settings:")
        self.stdout.write(f"  Backend: {email_settings.email_backend}")
        self.stdout.write(f"  Host: {email_settings.email_host}")
        self.stdout.write(f"  Port: {email_settings.email_port}")
        self.stdout.write(f"  Username: {email_settings.email_host_user}")
        self.stdout.write(
            f"  Password: {'*' * len(email_settings.email_host_password) if email_settings.email_host_password else 'None'}"
        )
        self.stdout.write(f"  TLS: {email_settings.email_use_tls}")
        self.stdout.write(f"  SSL: {email_settings.email_use_ssl}")
        self.stdout.write(f"  From Email: {email_settings.default_from_email}")

        # Check if Gmail-specific settings are correct
        if email_settings.email_host == "smtp.gmail.com":
            self.stdout.write(
                "\n"
                + self.style.WARNING(
                    "Gmail detected. Performing Gmail-specific checks..."
                )
            )

            # Check for common issues
            issues_found = False

            if (
                not email_settings.email_host_user
                or "@" not in email_settings.email_host_user
            ):
                self.stdout.write(
                    self.style.ERROR(
                        "  ❌ Invalid Gmail username. Must be a full email address."
                    )
                )
                issues_found = True
            else:
                self.stdout.write(
                    self.style.SUCCESS("  ✅ Valid Gmail username format.")
                )

            if email_settings.email_port not in [587, 465]:
                self.stdout.write(
                    self.style.ERROR(
                        "  ❌ Incorrect port. Gmail uses 587 (TLS) or 465 (SSL)."
                    )
                )
                issues_found = True
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ Correct port ({email_settings.email_port})."
                    )
                )

            if email_settings.email_use_tls and email_settings.email_use_ssl:
                self.stdout.write(
                    self.style.ERROR(
                        "  ❌ Both TLS and SSL enabled. Only one should be enabled."
                    )
                )
                issues_found = True
            elif not email_settings.email_use_tls and not email_settings.email_use_ssl:
                self.stdout.write(
                    self.style.WARNING(
                        "  ⚠️ Neither TLS nor SSL enabled. Consider enabling TLS for Gmail."
                    )
                )
            else:
                protocol = "TLS" if email_settings.email_use_tls else "SSL"
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ {protocol} correctly enabled.")
                )

            # Check password length (app passwords are usually 16 characters)
            if email_settings.email_host_password:
                if len(email_settings.email_host_password) < 10:
                    self.stdout.write(
                        self.style.WARNING(
                            "  ⚠️ Password seems short. For Gmail, use a 16-character App Password."
                        )
                    )
                elif len(email_settings.email_host_password) == 16:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "  ✅ Password length suggests App Password."
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            "  ⚠️ Password length unusual for Gmail App Password (typically 16 chars)."
                        )
                    )
            else:
                self.stdout.write(self.style.ERROR("  ❌ No password set."))
                issues_found = True

            if not issues_found:
                self.stdout.write(
                    self.style.SUCCESS("  ✅ All Gmail settings appear correct.")
                )

            # Provide recommendations
            self.stdout.write("\nRecommendations:")
            self.stdout.write(
                "1. Ensure 2-Factor Authentication is enabled on your Google account"
            )
            self.stdout.write(
                "2. Generate an App Password specifically for this application:"
            )
            self.stdout.write("   - Go to your Google Account settings")
            self.stdout.write(
                "   - Navigate to Security → 2-Step Verification → App passwords"
            )
            self.stdout.write("   - Generate a new app password for 'Mail'")
            self.stdout.write(
                "3. Use the 16-character App Password instead of your regular Gmail password"
            )
            self.stdout.write(
                "4. Never use your regular Gmail password with SMTP - it won't work"
            )

        # Test email sending if requested
        if options["test_email"]:
            self.stdout.write(f"\nTesting email sending to {options['test_email']}...")
            self.test_email_sending(options["test_email"])

    def test_email_sending(self, test_email):
        try:
            # Apply email settings
            apply_email_settings()

            # Send test email
            send_mail(
                "Gmail Troubleshooting Test",
                "This is a test email to verify Gmail configuration.",
                settings.DEFAULT_FROM_EMAIL,
                [test_email],
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ Email sent successfully! Gmail configuration appears to be working."
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to send email: {e}"))
            self.stdout.write("\nCommon solutions:")
            self.stdout.write(
                "- Generate a Gmail App Password and use it instead of your regular password"
            )
            self.stdout.write(
                "- Ensure 2-Factor Authentication is enabled on your Google account"
            )
            self.stdout.write("- Check that your Gmail address is correctly entered")
            self.stdout.write(
                "- Verify that you're using the correct port (587 for TLS)"
            )
