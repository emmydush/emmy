from django.core.management.base import BaseCommand
from settings.models import EmailSettings

class Command(BaseCommand):
    help = "Setup email configuration for the application"

    def add_arguments(self, parser):
        parser.add_argument('--backend', type=str, choices=['smtp', 'console', 'ses'], default='smtp', help='Email backend')
        parser.add_argument('--host', type=str, help='Email host (e.g., smtp.gmail.com)')
        parser.add_argument('--port', type=int, default=587, help='Email port (default: 587)')
        parser.add_argument('--username', type=str, help='Email username')
        parser.add_argument('--password', type=str, help='Email password or app password')
        parser.add_argument('--from-email', type=str, help='Default from email address')
        parser.add_argument('--use-tls', action='store_true', help='Use TLS encryption')
        parser.add_argument('--use-ssl', action='store_true', help='Use SSL encryption')

    def handle(self, *args, **options):
        # Get or create email settings
        email_settings, created = EmailSettings.objects.get_or_create(id=1)
        
        # Set backend
        if options['backend'] == 'smtp':
            email_settings.email_backend = "django.core.mail.backends.smtp.EmailBackend"
        elif options['backend'] == 'console':
            email_settings.email_backend = "django.core.mail.backends.console.EmailBackend"
        elif options['backend'] == 'ses':
            email_settings.email_backend = "django_ses.SESBackend"
        
        # Update settings if provided (only for SMTP)
        if options['backend'] == 'smtp':
            if options['host']:
                email_settings.email_host = options['host']
            if options['port']:
                email_settings.email_port = options['port']
            if options['username']:
                email_settings.email_host_user = options['username']
            if options['password']:
                email_settings.email_host_password = options['password']
            if options['from_email']:
                email_settings.default_from_email = options['from_email']
            if options['use_tls']:
                email_settings.email_use_tls = True
                email_settings.email_use_ssl = False
            if options['use_ssl']:
                email_settings.email_use_ssl = True
                email_settings.email_use_tls = False
                
        # For console backend, clear sensitive fields
        if options['backend'] == 'console':
            email_settings.email_host = None
            email_settings.email_port = 587
            email_settings.email_host_user = None
            email_settings.email_host_password = None
            email_settings.email_use_tls = False
            email_settings.email_use_ssl = False
        
        # Save settings
        email_settings.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Email settings {'created' if created else 'updated'} successfully!"
            )
        )
        
        # Show current settings
        self.stdout.write("Current email settings:")
        self.stdout.write(f"  Backend: {email_settings.email_backend}")
        if email_settings.email_backend == "django.core.mail.backends.smtp.EmailBackend":
            self.stdout.write(f"  Host: {email_settings.email_host}")
            self.stdout.write(f"  Port: {email_settings.email_port}")
            self.stdout.write(f"  Username: {email_settings.email_host_user}")
            self.stdout.write(f"  TLS: {email_settings.email_use_tls}")
            self.stdout.write(f"  SSL: {email_settings.email_use_ssl}")
        self.stdout.write(f"  From Email: {email_settings.default_from_email}")