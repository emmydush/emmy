from django.conf import settings
from .models import EmailSettings


def apply_email_settings():
    """
    Apply email settings from the database to Django's email configuration.
    This function should be called before sending emails to ensure the correct
    email configuration is used.
    """
    try:
        email_settings = EmailSettings.objects.get(id=1)
    except EmailSettings.DoesNotExist:
        # If no email settings exist, use default settings from local_settings.py
        return

    # Apply email settings to Django's configuration
    settings.EMAIL_BACKEND = email_settings.email_backend
    settings.EMAIL_HOST = email_settings.email_host
    settings.EMAIL_PORT = email_settings.email_port
    settings.EMAIL_HOST_USER = email_settings.email_host_user
    settings.EMAIL_HOST_PASSWORD = email_settings.email_host_password
    settings.EMAIL_USE_TLS = email_settings.email_use_tls
    settings.EMAIL_USE_SSL = email_settings.email_use_ssl
    settings.DEFAULT_FROM_EMAIL = email_settings.default_from_email


def get_email_settings():
    """
    Get email settings from the database.
    Returns a dictionary with email configuration.
    """
    try:
        email_settings = EmailSettings.objects.get(id=1)
        return {
            "EMAIL_BACKEND": email_settings.email_backend,
            "EMAIL_HOST": email_settings.email_host,
            "EMAIL_PORT": email_settings.email_port,
            "EMAIL_HOST_USER": email_settings.email_host_user,
            "EMAIL_HOST_PASSWORD": email_settings.email_host_password,
            "EMAIL_USE_TLS": email_settings.email_use_tls,
            "EMAIL_USE_SSL": email_settings.email_use_ssl,
            "DEFAULT_FROM_EMAIL": email_settings.default_from_email,
        }
    except EmailSettings.DoesNotExist:
        # Return default settings
        return {
            "EMAIL_BACKEND": getattr(
                settings,
                "EMAIL_BACKEND",
                "django.core.mail.backends.console.EmailBackend",
            ),
            "EMAIL_HOST": getattr(settings, "EMAIL_HOST", None),
            "EMAIL_PORT": getattr(settings, "EMAIL_PORT", 587),
            "EMAIL_HOST_USER": getattr(settings, "EMAIL_HOST_USER", None),
            "EMAIL_HOST_PASSWORD": getattr(settings, "EMAIL_HOST_PASSWORD", None),
            "EMAIL_USE_TLS": getattr(settings, "EMAIL_USE_TLS", True),
            "EMAIL_USE_SSL": getattr(settings, "EMAIL_USE_SSL", False),
            "DEFAULT_FROM_EMAIL": getattr(
                settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost"
            ),
        }


def log_activity(
    user=None,
    action=None,
    model_name=None,
    object_id=None,
    object_repr=None,
    change_message=None,
    request=None,
):
    """
    Log an activity to the audit log.

    Args:
        user: The user performing the action
        action: The type of action (CREATE, UPDATE, DELETE, etc.)
        model_name: The name of the model being affected
        object_id: The ID of the object being affected
        object_repr: A string representation of the object
        change_message: Details about what changed
        request: The HTTP request object (for IP and user agent)
    """
    from .models import AuditLog

    # Get IP address and user agent from request if available
    ip_address = None
    user_agent = None
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]  # Limit to 255 chars

    # Create the audit log entry
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        change_message=change_message,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def get_client_ip(request):
    """
    Get the client's IP address from the request.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
