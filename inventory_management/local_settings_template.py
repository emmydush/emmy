"""
Local Settings Template for Inventory Management System

Copy this file to 'local_settings.py' and configure your database settings.

For production deployment, you must configure a PostgreSQL database.
For local development, you can use SQLite (not recommended for production).
"""

# PostgreSQL Database Configuration (Recommended for Production)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "your_database_name",
        "USER": "your_database_user",
        "PASSWORD": "your_database_password",
        "HOST": "localhost",  # Or your database host
        "PORT": "5432",  # Default PostgreSQL port
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Alternative: SQLite Configuration (NOT recommended for production)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': 'db.sqlite3',
#     }
# }

# Security Settings - Update for production
SECRET_KEY = "your-secret-key-here-change-this-in-production"
DEBUG = True  # Set to False in production
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "*"]  # Add your domain in production

# Email Configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.your-email-provider.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "your-email@example.com"
EMAIL_HOST_PASSWORD = "your-email-password"

# Additional Production Settings
# SECURE_SSL_REDIRECT = True  # Enable in production with SSL
# SECURE_HSTS_SECONDS = 31536000  # Enable in production
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Enable in production
# SECURE_HSTS_PRELOAD = True  # Enable in production
