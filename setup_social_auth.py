#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_management.settings")
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


def setup_social_auth():
    # Get or create the current site
    site, created = Site.objects.get_or_create(
        domain="localhost:8000", defaults={"name": "Inventory Management System"}
    )

    # Facebook
    facebook_app, created = SocialApp.objects.get_or_create(
        provider="facebook",
        defaults={
            "name": "Facebook",
            "client_id": "your-facebook-client-id",
            "secret": "your-facebook-secret",
        },
    )
    if site not in facebook_app.sites.all():
        facebook_app.sites.add(site)

    # Google
    google_app, created = SocialApp.objects.get_or_create(
        provider="google",
        defaults={
            "name": "Google",
            "client_id": "your-google-client-id",
            "secret": "your-google-secret",
        },
    )
    if site not in google_app.sites.all():
        google_app.sites.add(site)

    # LinkedIn
    linkedin_app, created = SocialApp.objects.get_or_create(
        provider="linkedin_oauth2",
        defaults={
            "name": "LinkedIn",
            "client_id": "your-linkedin-client-id",
            "secret": "your-linkedin-secret",
        },
    )
    if site not in linkedin_app.sites.all():
        linkedin_app.sites.add(site)

    print("Social authentication providers configured successfully!")
    print("Please update the client IDs and secrets in the Django admin panel.")


if __name__ == "__main__":
    setup_social_auth()
