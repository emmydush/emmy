from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import (
    Business,
    SubscriptionPlan,
    Subscription,
    Payment,
    SystemSetting,
    SystemLog,
    SecurityEvent,
    Announcement,
    SupportTicket,
    APIClient,
    APIRequestLog,
)
from authentication.models import User
from .middleware import set_current_business


def is_superadmin(user):
    return user.is_superuser


@method_decorator(
    [staff_member_required, user_passes_test(is_superadmin)], name="dispatch"
)
class SuperAdminDashboardView(TemplateView):
    template_name = "superadmin/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Business & User Management stats
        context["total_businesses"] = Business.objects.count()
        context["active_businesses"] = Business.objects.filter(status="active").count()
        context["pending_businesses"] = Business.objects.filter(
            status="pending"
        ).count()
        context["suspended_businesses"] = Business.objects.filter(
            status="suspended"
        ).count()
        context["total_users"] = User.objects.count()

        # Subscription & Billing stats
        context["total_subscriptions"] = Subscription.objects.count()
        context["active_subscriptions"] = Subscription.objects.filter(
            is_active=True
        ).count()
        context["total_revenue"] = (
            Payment.objects.filter(status="completed").aggregate(total=Sum("amount"))[
                "total"
            ]
            or 0
        )

        # System stats
        context["total_logs"] = SystemLog.objects.count()
        context["security_events"] = SecurityEvent.objects.filter(
            is_resolved=False
        ).count()
        context["open_tickets"] = SupportTicket.objects.filter(status="open").count()

        # Recent activities
        context["recent_businesses"] = Business.objects.order_by("-created_at")[:5]
        context["recent_users"] = User.objects.order_by("-date_joined")[:5]
        context["recent_logs"] = SystemLog.objects.order_by("-timestamp")[:10]

        # Security monitoring
        context["recent_security_events"] = SecurityEvent.objects.order_by(
            "-timestamp"
        )[:10]
        context["unresolved_security_events"] = SecurityEvent.objects.filter(
            is_resolved=False
        ).count()
        context["suspended_users"] = User.objects.filter(is_active=False).count()

        # API monitoring
        context["api_clients"] = APIClient.objects.count()
        context["active_api_clients"] = APIClient.objects.filter(is_active=True).count()

        return context


@method_decorator(
    [staff_member_required, user_passes_test(is_superadmin)], name="dispatch"
)
class BusinessManagementView(TemplateView):
    template_name = "superadmin/business_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["businesses"] = Business.objects.all()
        context["users"] = User.objects.all()
        return context


@method_decorator(
    [staff_member_required, user_passes_test(is_superadmin)], name="dispatch"
)
class SubscriptionManagementView(TemplateView):
    template_name = "superadmin/subscription_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plans"] = SubscriptionPlan.objects.all()
        context["subscriptions"] = Subscription.objects.all()
        context["payments"] = Payment.objects.all()
        return context


@method_decorator(
    [staff_member_required, user_passes_test(is_superadmin)], name="dispatch"
)
class SystemLogsView(TemplateView):
    template_name = "superadmin/system_logs.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["logs"] = SystemLog.objects.all()
        context["security_events"] = SecurityEvent.objects.all()
        return context


@method_decorator(
    [staff_member_required, user_passes_test(is_superadmin)], name="dispatch"
)
class CommunicationCenterView(TemplateView):
    template_name = "superadmin/communication_center.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["announcements"] = Announcement.objects.all()
        context["tickets"] = SupportTicket.objects.all()
        return context


@method_decorator(
    [staff_member_required, user_passes_test(is_superadmin)], name="dispatch"
)
class APIMonitoringView(TemplateView):
    template_name = "superadmin/api_monitoring.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["api_clients"] = APIClient.objects.all()
        context["api_logs"] = APIRequestLog.objects.all()
        return context


# Business selection view for regular users
def business_selection_view(request):
    """
    View to allow users to select which business they want to work with.
    This is crucial for multi-tenancy data isolation.
    """
    # Get businesses that the user has access to
    # For now, we'll assume users can access businesses they own
    # In a more complex system, you might have a many-to-many relationship
    # between users and businesses with roles
    user_businesses = Business.objects.filter(owner=request.user)

    if request.method == "POST":
        business_id = request.POST.get("business_id")
        if business_id:
            try:
                business = Business.objects.get(id=business_id, owner=request.user)
                # Store the selected business in the session
                request.session["current_business_id"] = business.id
                # Also set in middleware thread-local storage
                set_current_business(business)
                # Redirect to the dashboard
                return redirect("dashboard:index")
            except Business.DoesNotExist:
                messages.error(request, "Invalid business selection.")
        else:
            messages.error(request, "Please select a business.")

    context = {"businesses": user_businesses}
    return render(request, "superadmin/business_selection.html", context)
