# Local development settings
# This file is used for local development and overrides production settings

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Use SQLite for local development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Development settings
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "*"]

# Use console email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Secret key for development (do not use in production)
SECRET_KEY = "django-insecure-local-dev-key-for-development-only-change-in-production"

# Disable SSL redirect for local development
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Media files for development
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
