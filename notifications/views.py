from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.timesince import timesince
from django.http import JsonResponse
from .models import Notification
from superadmin.middleware import get_current_business


@login_required
def notification_list(request):
    # Filter notifications by business context
    current_business = get_current_business()
    if current_business:
        notifications = Notification.objects.filter(
            recipient=request.user, business=current_business
        )
    else:
        notifications = Notification.objects.filter(recipient=request.user)

    unread_count = notifications.filter(is_read=False).count()

    return render(
        request,
        "notifications/list.html",
        {"notifications": notifications, "unread_count": unread_count},
    )


@login_required
def mark_as_read(request, pk):
    # Ensure notification belongs to user and business context
    current_business = get_current_business()
    notification_filter = {"pk": pk, "recipient": request.user}
    if current_business:
        notification_filter["business"] = current_business

    notification = get_object_or_404(Notification, **notification_filter)
    notification.mark_as_read()
    return redirect("notifications:list")


@login_required
def mark_all_as_read(request):
    # Mark all notifications as read for user and business context
    current_business = get_current_business()
    notification_filter = {"recipient": request.user, "is_read": False}
    if current_business:
        notification_filter["business"] = current_business

    Notification.objects.filter(**notification_filter).update(
        is_read=True, read_at=timezone.now()
    )
    messages.success(request, "All notifications marked as read.")
    return redirect("notifications:list")


@login_required
def unread_notifications(request):
    """Return JSON response with unread notifications for AJAX dropdown"""
    # Filter by business context
    current_business = get_current_business()
    notification_filter = {"recipient": request.user, "is_read": False}
    if current_business:
        notification_filter["business"] = current_business

    unread_notifications = Notification.objects.filter(**notification_filter).order_by(
        "-created_at"
    )[
        :5
    ]  # Limit to 5 most recent

    notifications_data = []
    for notification in unread_notifications:
        notifications_data.append(
            {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "type": notification.get_notification_type_display(),
                "created_at": notification.created_at.strftime("%Y-%m-%d %H:%M"),
                "time_since": (
                    timesince(notification.created_at)
                    if notification.created_at
                    else "Unknown time"
                ),
            }
        )

    return JsonResponse(
        {"notifications": notifications_data, "count": len(notifications_data)}
    )
