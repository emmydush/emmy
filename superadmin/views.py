from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.db.models import Sum
from superadmin.models import Business, Branch, Subscription, Payment, SystemLog, SecurityEvent
from settings.models import EmailSettings
from datetime import datetime, timedelta

User = get_user_model()

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
        context["security_events"] = SecurityEvent.objects.count()
        context["open_tickets"] = 5  # Placeholder value
        context["api_clients"] = 12  # Placeholder value
        context["active_api_clients"] = 8  # Placeholder value
        context["total_transactions"] = 1250  # Placeholder value
        context["todays_transactions"] = 42  # Placeholder value
        context["total_stock_items"] = 5420  # Placeholder value

        # System uptime (placeholder - in a real app, you'd calculate this)
        context["system_uptime"] = "99.9%"

        # Recent security events (last 5)
        context["recent_security_events"] = SecurityEvent.objects.order_by(
            "-timestamp"
        )[:5]

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


# Branch selection view for regular users
def branch_selection_view(request):
    """
    View to allow users to select which branch they want to work with.
    This is crucial for multi-branch functionality.
    """
    # Get the current business from the session
    business_id = request.session.get("current_business_id")
    if not business_id:
        messages.error(request, "Please select a business first.")
        return redirect("superadmin:business_selection")
    
    try:
        business = Business.objects.get(id=business_id)
        # Set the business context
        set_current_business(business)
    except Business.DoesNotExist:
        messages.error(request, "Invalid business selection.")
        return redirect("superadmin:business_selection")
    
    # Get branches for the current business
    branches = Branch.objects.filter(business=business, is_active=True)
    
    # Check if user has branch restrictions
    try:
        user_permission = UserPermission.objects.get(user=request.user)
        if user_permission.restrict_to_assigned_branches:
            # Filter branches to only those assigned to the user
            branches = branches.filter(user_permissions=user_permission)
    except UserPermission.DoesNotExist:
        # If no custom permissions exist, user can access all branches
        pass
    
    # If there's only one branch, automatically select it
    if branches.count() == 1:
        branch = branches.first()
        request.session["current_branch_id"] = branch.id
        # Store the selected branch in the session
        # We'll handle the branch context in middleware
        return redirect("dashboard:index")
    
    # If there's no branch, redirect to create one
    if not branches.exists():
        messages.info(request, "No branches found for this business. Please create a branch first.")
        return redirect("superadmin:branch_list", business_pk=business.pk)

    if request.method == "POST":
        branch_id = request.POST.get("branch_id")
        if branch_id:
            try:
                branch = Branch.objects.get(id=branch_id, business=business, is_active=True)
                # Check if user has permission to access this branch
                try:
                    user_permission = UserPermission.objects.get(user=request.user)
                    if user_permission.restrict_to_assigned_branches:
                        if not user_permission.branches.filter(id=branch_id).exists():
                            messages.error(request, "You do not have permission to access this branch.")
                            context = {
                                "business": business,
                                "branches": branches,
                            }
                            return render(request, "superadmin/branch_selection.html", context)
                except UserPermission.DoesNotExist:
                    # If no custom permissions exist, user can access all branches
                    pass
                
                # Store the selected branch in the session
                request.session["current_branch_id"] = branch.id
                # Redirect to the dashboard
                return redirect("dashboard:index")
            except Branch.DoesNotExist:
                messages.error(request, "Invalid branch selection.")
        else:
            messages.error(request, "Please select a branch.")

    context = {
        "business": business,
        "branches": branches,
    }
    return render(request, "superadmin/branch_selection.html", context)


# Add Branch Management Views
@login_required
def branch_list_view(request, business_pk):
    """Display list of branches for a specific business"""
    business = get_object_or_404(Business, pk=business_pk)
    
    # Check if user has permission to access this business
    if request.user != business.owner and not request.user.is_superuser:
        messages.error(request, "You do not have permission to access this business.")
        return redirect("dashboard:index")
    
    branches = Branch.objects.filter(business=business)
    
    # Count active branches
    active_branches_count = branches.filter(is_active=True).count()
    
    context = {
        "business": business,
        "branches": branches,
        "active_branches_count": active_branches_count,
    }
    
    # Use different templates for superadmins vs business owners
    if request.user.is_superuser:
        template = "superadmin/branches/list.html"
    else:
        template = "business_owner/branches/list.html"
    
    return render(request, template, context)


@login_required
def branch_create_view(request, business_pk):
    """Create a new branch for a specific business"""
    business = get_object_or_404(Business, pk=business_pk)
    
    # Check if user has permission to access this business
    if request.user != business.owner and not request.user.is_superuser:
        messages.error(request, "You do not have permission to access this business.")
        return redirect("dashboard:index")
    
    if request.method == "POST":
        form = BranchForm(request.POST, business=business)
        if form.is_valid():
            branch = form.save(commit=False)
            branch.business = business
            branch.save()
            messages.success(request, "Branch created successfully!")
            return redirect("superadmin:branch_list", business_pk=business.pk)
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = BranchForm(business=business)
    
    context = {
        "form": form,
        "business": business,
        "title": "Create Branch",
    }
    
    # Use different templates for superadmins vs business owners
    if request.user.is_superuser:
        template = "superadmin/branches/form.html"
    else:
        template = "business_owner/branches/form.html"
    
    return render(request, template, context)


@login_required
def branch_update_view(request, business_pk, pk):
    """Update a specific branch"""
    business = get_object_or_404(Business, pk=business_pk)
    branch = get_object_or_404(Branch, pk=pk, business=business)
    
    # Check if user has permission to access this business
    if request.user != business.owner and not request.user.is_superuser:
        messages.error(request, "You do not have permission to access this business.")
        return redirect("dashboard:index")
    
    if request.method == "POST":
        form = BranchForm(request.POST, instance=branch, business=business)
        if form.is_valid():
            form.save()
            messages.success(request, "Branch updated successfully!")
            return redirect("superadmin:branch_list", business_pk=business.pk)
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = BranchForm(instance=branch, business=business)
    
    context = {
        "form": form,
        "business": business,
        "branch": branch,
        "title": "Update Branch",
    }
    
    # Use different templates for superadmins vs business owners
    if request.user.is_superuser:
        template = "superadmin/branches/form.html"
    else:
        template = "business_owner/branches/form.html"
    
    return render(request, template, context)


@login_required
def branch_delete_view(request, business_pk, pk):
    """Delete a specific branch"""
    business = get_object_or_404(Business, pk=business_pk)
    branch = get_object_or_404(Branch, pk=pk, business=business)
    
    # Check if user has permission to access this business
    if request.user != business.owner and not request.user.is_superuser:
        messages.error(request, "You do not have permission to access this business.")
        return redirect("dashboard:index")
    
    if request.method == "POST":
        branch_name = branch.name
        branch.delete()
        messages.success(request, f"Branch '{branch_name}' deleted successfully!")
        return redirect("superadmin:branch_list", business_pk=business.pk)
    
    context = {
        "business": business,
        "branch": branch,
    }
    
    # Use different templates for superadmins vs business owners
    if request.user.is_superuser:
        template = "superadmin/branches/confirm_delete.html"
    else:
        template = "business_owner/branches/confirm_delete.html"
    
    return render(request, template, context)


@staff_member_required
@user_passes_test(lambda u: u.is_superuser)
def approve_business_view(request, business_pk):
    """Approve a pending business"""
    business = get_object_or_404(Business, pk=business_pk)
    
    if request.method == "POST":
        business.status = "active"
        business.save()
        
        # Create or update UserPermission for the business owner
        if business.owner:
            from authentication.models import UserPermission
            user_permission, created = UserPermission.objects.get_or_create(user=business.owner)
            
            # Set default permissions for business owners
            user_permission.can_create = True
            user_permission.can_edit = True
            user_permission.can_delete = True
            user_permission.can_manage_users = True
            user_permission.can_create_users = True
            user_permission.can_edit_users = True
            user_permission.can_delete_users = True
            user_permission.can_access_products = True
            user_permission.can_access_sales = True
            user_permission.can_access_purchases = True
            user_permission.can_access_customers = True
            user_permission.can_access_suppliers = True
            user_permission.can_access_expenses = True
            user_permission.can_access_reports = True
            user_permission.can_access_settings = True
            user_permission.save()
        
        messages.success(request, f"Business '{business.company_name}' has been approved and activated.")
        
        # Send approval email
        send_business_status_email(request, business, "approved")
        
        return redirect("superadmin:business_management")
    
    context = {
        "business": business,
        "action": "approve",
    }
    return render(request, "superadmin/confirm_business_action.html", context)


@staff_member_required
@user_passes_test(lambda u: u.is_superuser)
def activate_business_view(request, business_pk):
    """Activate a suspended business"""
    business = get_object_or_404(Business, pk=business_pk)
    
    if request.method == "POST":
        business.status = "active"
        business.save()
        messages.success(request, f"Business '{business.company_name}' has been activated.")
        
        # Send activation email
        send_business_status_email(request, business, "activated")
        
        return redirect("superadmin:business_management")
    
    context = {
        "business": business,
        "action": "activate",
    }
    return render(request, "superadmin/confirm_business_action.html", context)


@staff_member_required
@user_passes_test(lambda u: u.is_superuser)
def suspend_business_view(request, business_pk):
    """Suspend a business"""
    business = get_object_or_404(Business, pk=business_pk)
    
    if request.method == "POST":
        business.status = "suspended"
        business.save()
        messages.success(request, f"Business '{business.company_name}' has been suspended.")
        
        # Send suspension email
        send_business_status_email(request, business, "suspended")
        
        return redirect("superadmin:business_management")
    
    context = {
        "business": business,
        "action": "suspend",
    }
    return render(request, "superadmin/confirm_business_action.html", context)


@staff_member_required
@user_passes_test(lambda u: u.is_superuser)
def delete_business_view(request, business_pk):
    """Delete a business"""
    business = get_object_or_404(Business, pk=business_pk)
    
    if request.method == "POST":
        business_name = business.company_name
        business.delete()
        messages.success(request, f"Business '{business_name}' has been deleted successfully.")
        return redirect("superadmin:business_management")
    
    context = {
        "business": business,
        "action": "delete",
    }
    return render(request, "superadmin/confirm_business_action.html", context)


def send_business_status_email(request, business, status):
    """Send email notification about business status change"""
    try:
        # Import here to avoid circular imports
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        from django.utils import timezone
        from settings.models import BusinessSettings
        
        # Get business-specific settings for email context
        try:
            business_settings = BusinessSettings.objects.get(business=business)
        except BusinessSettings.DoesNotExist:
            # Fall back to global settings
            try:
                business_settings = BusinessSettings.objects.get(id=1)
            except BusinessSettings.DoesNotExist:
                business_settings = BusinessSettings.objects.create(
                    id=1,
                    business_name="Smart Solution",
                    business_address="123 Business Street, City, Country",
                    business_email="info@smartsolution.com",
                    business_phone="+1 (555) 123-4567",
                    currency="FRW",
                    currency_symbol="FRW",
                    tax_rate=0,
                )
        
        # Check if business has an owner with an email
        if not business.owner or not business.owner.email:
            return  # No email to send to
            
        # Prepare email context
        context = {
            "business": business,
            "business_settings": business_settings,
            "status": status,
            "login_url": request.build_absolute_uri("/accounts/login/"),
            "current_year": timezone.now().year,
        }
        
        # Render email templates
        subject = f"[{business_settings.business_name}] Business Account {status.title()}"
        html_message = render_to_string("emails/business_approval.html", context)
        plain_message = render_to_string("emails/business_approval.txt", context)
        
        # Send email
        send_mail(
            subject,
            plain_message,
            business_settings.business_email or settings.DEFAULT_FROM_EMAIL,
            [business.owner.email],
            html_message=html_message,
            fail_silently=True,  # Don't crash if email fails
        )
    except Exception as e:
        # Log the error but don't crash the main flow
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send business status email: {str(e)}")


def send_business_registration_email(request, business, owner):
    """Send email notification about business registration"""
    try:
        # Import here to avoid circular imports
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        from django.utils import timezone
        from settings.models import BusinessSettings
        
        # Get business-specific settings for email context
        try:
            business_settings = BusinessSettings.objects.get(business=business)
        except BusinessSettings.DoesNotExist:
            # Fall back to global settings
            try:
                business_settings = BusinessSettings.objects.get(id=1)
            except BusinessSettings.DoesNotExist:
                business_settings = BusinessSettings.objects.create(
                    id=1,
                    business_name="Smart Solution",
                    business_address="123 Business Street, City, Country",
                    business_email="info@smartsolution.com",
                    business_phone="+1 (555) 123-4567",
                    currency="FRW",
                    currency_symbol="FRW",
                    tax_rate=0,
                )
        
        # Check if owner has an email
        if not owner.email:
            return  # No email to send to
            
        # Prepare email context
        context = {
            "business": business,
            "business_settings": business_settings,
            "owner": owner,
            "login_url": request.build_absolute_uri("/accounts/login/"),
            "current_year": timezone.now().year,
        }
        
        # Render email templates
        subject = f"[{business_settings.business_name}] Business Registration Confirmation"
        html_message = render_to_string("emails/business_registration.html", context)
        plain_message = render_to_string("emails/business_registration.txt", context)
        
        # Send email
        send_mail(
            subject,
            plain_message,
            business_settings.business_email or settings.DEFAULT_FROM_EMAIL,
            [owner.email],
            html_message=html_message,
            fail_silently=True,  # Don't crash if email fails
        )
    except Exception as e:
        # Log the error but don't crash the main flow
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send business registration email: {str(e)}")


def business_register_view(request):
    """Handle business registration"""
    if request.method == "POST":
        form = BusinessRegistrationForm(request.POST)
        if form.is_valid():
            # Save the business with pending status
            business = form.save()
            
            # Create business settings with the company name
            from settings.models import BusinessSettings
            BusinessSettings.objects.create(
                business=business,
                business_name=business.company_name,
                business_email=business.email,
                # Other fields will use their default values
            )
            
            # Create owner user if email is provided
            owner_email = form.cleaned_data.get("owner_email")
            if owner_email:
                try:
                    # Create owner user
                    owner_username = owner_email.split("@")[0]
                    # Ensure username is unique
                    counter = 1
                    original_username = owner_username
                    while User.objects.filter(username=owner_username).exists():
                        owner_username = f"{original_username}_{counter}"
                        counter += 1
                    
                    owner = User.objects.create_user(
                        username=owner_username,
                        email=owner_email,
                        password=User.objects.make_random_password(),
                        is_staff=False,
                        is_superuser=False
                    )
                    
                    # Associate owner with business
                    business.owner = owner
                    business.save()
                    
                    # Send email to owner with instructions to set password
                    send_business_registration_email(request, business, owner)
                    
                except Exception as e:
                    messages.error(request, f"Error creating owner account: {str(e)}")
            
            messages.success(request, "Business registration submitted successfully. Our team will review your application and approve it shortly.")
            return redirect("superadmin:business_registration_success")
    else:
        form = BusinessRegistrationForm()
    
    context = {
        "form": form,
    }
    return render(request, "superadmin/business_register.html", context)


def business_registration_success_view(request):
    """Show business registration success page"""
    return render(request, "superadmin/business_registration_success.html")


@login_required
def branch_request_list_view(request):
    """Display list of branch requests for the current business"""
    # Get current business from session
    business_id = request.session.get("current_business_id")
    if not business_id:
        messages.error(request, "Please select a business first.")
        return redirect("superadmin:business_selection")
    
    try:
        business = Business.objects.get(id=business_id)
    except Business.DoesNotExist:
        messages.error(request, "Invalid business selection.")
        return redirect("superadmin:business_selection")
    
    # Get branch requests for this business
    branch_requests = BranchRequest.objects.filter(business=business)
    
    context = {
        "business": business,
        "branch_requests": branch_requests,
    }
    return render(request, "superadmin/branches/request_list.html", context)


@login_required
def branch_request_create_view(request):
    """Create a new branch request for the current business"""
    
    # Get current business from session
    business_id = request.session.get("current_business_id")
    if not business_id:
        messages.error(request, "Please select a business first.")
        return redirect("superadmin:business_selection")
    
    try:
        business = Business.objects.get(id=business_id)
    except Business.DoesNotExist:
        messages.error(request, "Invalid business selection.")
        return redirect("superadmin:business_selection")
    
    # Check if user is business owner or admin
    if request.user != business.owner and request.user.role != "admin":
        messages.error(request, "You do not have permission to create branch requests for this business.")
        return redirect("dashboard:index")
    
    if request.method == "POST":
        form = BranchRequestForm(request.POST, business=business)
        if form.is_valid():
            branch_request = form.save(commit=False)
            branch_request.business = business
            branch_request.requested_by = request.user
            branch_request.save()
            messages.success(request, "Branch request submitted successfully! It is now pending approval by a superadmin.")
            return redirect("superadmin:branch_request_list")
        else:
            # Form is not valid, display errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = BranchRequestForm(business=business)
    
    context = {
        "form": form,
        "business": business,
        "title": "Request New Branch",
    }
    return render(request, "superadmin/branches/request_form.html", context)


@staff_member_required
@user_passes_test(lambda u: u.is_superuser)
def branch_request_approval_list_view(request):
    """Display list of pending branch requests for superadmins"""
    # Get all pending branch requests
    pending_requests = BranchRequest.objects.filter(status="pending")
    
    context = {
        "pending_requests": pending_requests,
    }
    return render(request, "superadmin/branches/approval_list.html", context)


@staff_member_required
@user_passes_test(lambda u: u.is_superuser)
def branch_request_approve_view(request, pk):
    """Approve or reject a branch request"""
    branch_request = get_object_or_404(BranchRequest, pk=pk)
    
    if request.method == "POST":
        form = BranchRequestApprovalForm(request.POST, instance=branch_request)
        if form.is_valid():
            branch_request = form.save(commit=False)
            branch_request.approved_by = request.user
            branch_request.approved_at = timezone.now()
            branch_request.save()
            
            if branch_request.status == "approved":
                messages.success(request, f"Branch request for '{branch_request.name}' has been approved and branch created successfully!")
            elif branch_request.status == "rejected":
                messages.success(request, f"Branch request for '{branch_request.name}' has been rejected.")
            
            return redirect("superadmin:branch_request_approval_list")
    else:
        form = BranchRequestApprovalForm(instance=branch_request)
    
    context = {
        "form": form,
        "branch_request": branch_request,
    }
    return render(request, "superadmin/branches/approve_request.html", context)


@staff_member_required
@user_passes_test(lambda u: u.is_superuser)
def branch_request_detail_view(request, pk):
    """View details of a branch request"""
    branch_request = get_object_or_404(BranchRequest, pk=pk)
    
    context = {
        "branch_request": branch_request,
    }
    return render(request, "superadmin/branches/request_detail.html", context)


@method_decorator(
    [staff_member_required, user_passes_test(is_superadmin)], name="dispatch"
)
class EmailSettingsView(TemplateView):
    template_name = "superadmin/email_settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get or create email settings
        email_settings, created = EmailSettings.objects.get_or_create(id=1)
        context["settings"] = email_settings
        context["form"] = EmailSettingsForm(instance=email_settings)
        return context

    def post(self, request, *args, **kwargs):
        # Get or create email settings
        email_settings, created = EmailSettings.objects.get_or_create(id=1)
        form = EmailSettingsForm(request.POST, instance=email_settings)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Email settings updated successfully!")
            return redirect("superadmin:email_settings")
        else:
            context = self.get_context_data()
            context["form"] = form
            return self.render_to_response(context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_user_view(request, user_id):
    """Delete a user"""
    user_to_delete = get_object_or_404(User, id=user_id)
    
    # Prevent users from deleting themselves
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect("superadmin:user_list")
    
    if request.method == "POST":
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f"User '{username}' has been deleted successfully.")
        return redirect("superadmin:user_list")
    
    context = {
        "user_to_delete": user_to_delete,
    }
    return render(request, "superadmin/users/confirm_delete.html", context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_user_view(request, user_id):
    """Edit a user"""
    user_to_edit = get_object_or_404(User, id=user_id)
    
    # Get all businesses for business assignment
    all_businesses = Business.objects.all()
    
    # Get user's assigned businesses
    assigned_businesses = user_to_edit.businesses.all()
    
    # Get all branches
    all_branches = Branch.objects.all()
    
    # Get user's assigned branches
    try:
        user_permission = UserPermission.objects.get(user=user_to_edit)
        assigned_branches = user_permission.branches.all()
    except UserPermission.DoesNotExist:
        assigned_branches = Branch.objects.none()
    
    if request.method == "POST":
        user_form = CustomUserChangeForm(request.POST, request.FILES, instance=user_to_edit)
        permission_form = UserPermissionForm(request.POST, instance=user_permission if 'user_permission' in locals() else None)
        
        if user_form.is_valid() and permission_form.is_valid():
            try:
                with transaction.atomic():
                    user = user_form.save()
                    
                    # Handle business assignments
                    selected_businesses = request.POST.getlist('businesses')
                    if selected_businesses:
                        businesses = Business.objects.filter(id__in=selected_businesses)
                        user.businesses.set(businesses)
                    
                    # Save or create user permissions
                    if hasattr(user_permission, 'id'):
                        permission = permission_form.save(commit=False)
                        permission.user = user
                        permission.save()
                    else:
                        permission = permission_form.save(commit=False)
                        permission.user = user
                        permission.save()
                    
                    # Handle branch assignments
                    selected_branches = request.POST.getlist('branches')
                    if selected_branches:
                        branches = Branch.objects.filter(id__in=selected_branches)
                        permission.branches.set(branches)
                    
                    messages.success(request, f"User {user.username} updated successfully!")
                    return redirect("superadmin:user_list")
            except Exception as e:
                messages.error(request, f"An error occurred while updating the user: {str(e)}")
        else:
            if user_form.errors:
                for field, errors in user_form.errors.items():
                    for error in errors:
                        messages.error(request, f"User form - {field}: {error}")
            if permission_form.errors:
                for field, errors in permission_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Permission form - {field}: {error}")
    else:
        user_form = CustomUserChangeForm(instance=user_to_edit)
        permission_form = UserPermissionForm(instance=user_permission if 'user_permission' in locals() else None)
    
    context = {
        "user_form": user_form,
        "permission_form": permission_form,
        "user_to_edit": user_to_edit,
        "all_businesses": all_businesses,
        "assigned_businesses": assigned_businesses,
        "all_branches": all_branches,
        "assigned_branches": assigned_branches,
    }
    return render(request, "superadmin/users/form.html", context)


@method_decorator(
    [staff_member_required, user_passes_test(lambda u: u.is_superuser)], name="dispatch"
)
class UserListView(TemplateView):
    template_name = "superadmin/users/list.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all users across all businesses
        context["users"] = User.objects.all().order_by('-date_joined')
        return context
