from .models import BusinessSettings
from typing import TYPE_CHECKING
from django.conf import settings

if TYPE_CHECKING:
    from django.db.models import QuerySet


def business_settings(request):
    """
    Context processor to add business settings to all templates
    """
    # Try to get business-specific settings first
    business_settings_obj = None
    
    # Try to get current business from session
    business_id = request.session.get("current_business_id")
    if business_id:
        try:
            from superadmin.models import Business
            business = Business.objects.get(id=business_id)
            if hasattr(business, 'settings'):
                business_settings_obj = business.settings
        except:
            pass
    
    # If no business-specific settings, try to get global settings
    if not business_settings_obj:
        try:
            business_settings_obj = BusinessSettings.objects.get(id=1)  # type: ignore
        except BusinessSettings.DoesNotExist:  # type: ignore
            # If no settings exist, create default ones
            business_settings_obj = BusinessSettings.objects.create(  # type: ignore
                id=1,
                business_name="Smart Solution",
                business_address="123 Business Street, City, Country",
                business_email="info@smartsolution.com",
                business_phone="+1 (555) 123-4567",
                currency="FRW",
                currency_symbol="FRW",
                tax_rate=0,
            )

    return {"business_settings": business_settings_obj}


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