import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_management.settings")
django.setup()

from settings.models import EmailSettings

def check_email_settings():
    print("Checking email settings...")
    try:
        email_settings = EmailSettings.objects.get(id=1)
        print("Email settings found:")
        print(f"  Backend: {email_settings.email_backend}")
        print(f"  Host: {email_settings.email_host}")
        print(f"  Port: {email_settings.email_port}")
        print(f"  User: {email_settings.email_host_user}")
        print(f"  TLS: {email_settings.email_use_tls}")
        print(f"  SSL: {email_settings.email_use_ssl}")
        print(f"  From: {email_settings.default_from_email}")
    except EmailSettings.DoesNotExist:
        print("No email settings found in database")
    except Exception as e:
        print(f"Error checking email settings: {e}")

if __name__ == "__main__":
    check_email_settings()