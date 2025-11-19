from .models import BusinessSettings
from typing import TYPE_CHECKING
from django.conf import settings

if TYPE_CHECKING:
    from django.db.models import QuerySet


def business_settings(request):
    """
    Context processor to add business settings to all templates
    """
    try:
        settings_obj = BusinessSettings.objects.get(id=1)  # type: ignore
    except BusinessSettings.DoesNotExist:  # type: ignore
        # If no settings exist, create default ones
        settings_obj = BusinessSettings.objects.create(  # type: ignore
            id=1,
            business_name="Smart Solution",
            business_address="123 Business Street, City, Country",
            business_email="info@smartsolution.com",
            business_phone="+1 (555) 123-4567",
            currency="FRW",
            currency_symbol="FRW",
            tax_rate=0,
        )

    return {"business_settings": settings_obj}


def notifications(request):
    """
    Context processor to add notification count to all templates
    """
    if request.user.is_authenticated:
        from notifications.models import Notification

        unread_count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return {"unread_notifications_count": unread_count}
    return {"unread_notifications_count": 0}


def media_settings(request):
    """
    Context processor to add media settings to all templates
    """
    return {"MEDIA_URL": settings.MEDIA_URL}
