from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, authenticate, login
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.db import transaction
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import translation
from django.http import HttpResponseRedirect
from django.conf import settings
from .forms import CustomUserCreationForm, CustomUserChangeForm, UserPermissionForm, UserProfileForm
from .models import User, UserPermission
from .utils import check_user_permission
from superadmin.models import Branch, Business
from superadmin.middleware import get_current_business


def custom_login_view(request):
    """
    Handle user login
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                # Redirect to dashboard or next URL
                next_url = request.GET.get('next', '/dashboard/')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'authentication/login.html', {'form': form})


@login_required
def profile(request):
    """
    Display and update user profile
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            # Redirect to appropriate profile based on user type
            if request.user.is_superuser:
                return redirect('superadmin:dashboard')
            else:
                return redirect('authentication:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=request.user)
    
    # Render appropriate template based on user type
    if request.user.is_superuser:
        return render(request, 'superadmin/profile.html', {'form': form})
    else:
        return render(request, 'authentication/profile.html', {'form': form})


@login_required
@require_http_methods(["POST"])
def set_user_language(request):
    """
    Set the user's preferred language.
    """
    user = request.user
    language = request.POST.get('language')
    next_url = request.POST.get('next', '/')
    
    # Validate language is in supported languages
    supported_languages = [lang[0] for lang in settings.LANGUAGES]
    if language and language in supported_languages:
        # Update user's language preference
        user.language = language
        user.save(update_fields=['language'])
        
        # Activate the language for the current session
        translation.activate(language)
        request.session[translation.LANGUAGE_SESSION_KEY] = language
    
    # Redirect to the next URL or dashboard
    return HttpResponseRedirect(next_url)


@login_required
def user_list(request):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_manage_users"
    ):
        messages.error(request, "You do not have permission to manage users.")
        return redirect("dashboard:index")

    # Get users for the current business
    current_business = get_current_business()
    if current_business:
        users = User.objects.filter(businesses=current_business)
    else:
        users = User.objects.none()

    context = {"users": users}
    return render(request, "authentication/user_list.html", context)


@login_required
def create_user(request):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_create_users"
    ):
        messages.error(request, "You do not have permission to create users.")
        return redirect("dashboard:index")

    # Get current business
    current_business = get_current_business()
    if not current_business:
        messages.error(request, "No business context found.")
        return redirect("dashboard:index")

    # Get all branches for this business
    all_branches = Branch.objects.filter(business=current_business)

    if request.method == "POST":
        user_form = CustomUserCreationForm(request.POST)
        permission_form = UserPermissionForm(request.POST)
        
        if user_form.is_valid() and permission_form.is_valid():
            try:
                with transaction.atomic():
                    # Save the user
                    user = user_form.save(current_business)
                    
                    # Save the permissions
                    permission = permission_form.save(commit=False)
                    permission.user = user
                    permission.save()
                    
                    # Handle branch assignments
                    selected_branches = request.POST.getlist('branches')
                    if selected_branches:
                        branches = Branch.objects.filter(
                            id__in=selected_branches, 
                            business=current_business
                        )
                        permission.branches.set(branches)
                    
                    messages.success(request, f"User {user.username} created successfully!")
                    return redirect("authentication:user_list")
            except Exception as e:
                messages.error(request, f"An error occurred while creating the user: {str(e)}")
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
        user_form = CustomUserCreationForm()
        permission_form = UserPermissionForm()

    context = {
        "user_form": user_form,
        "permission_form": permission_form,
        "all_branches": all_branches,
    }
    return render(request, "authentication/create_user_styled.html", context)


@login_required
def edit_user(request, user_id):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_edit_users"
    ):
        messages.error(request, "You do not have permission to edit users.")
        return redirect("dashboard:index")

    user_to_edit = get_object_or_404(User, id=user_id)
    
    # Get current business
    current_business = get_current_business()
    
    # Get all branches for this business
    all_branches = Branch.objects.filter(business=current_business) if current_business else Branch.objects.none()
    
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
                    
                    # Save or create user permissions
                    if hasattr(user_permission, 'id'):
                        permission = permission_form.save(commit=False)
                        permission.user = user
                        permission.save()
                        permission_form.save_m2m()  # Save many-to-many relationships
                    else:
                        permission = permission_form.save(commit=False)
                        permission.user = user
                        permission.save()
                        permission_form.save_m2m()  # Save many-to-many relationships
                    
                    # Handle branch assignments
                    if 'branches' in request.POST:
                        selected_branches = request.POST.getlist('branches')
                        permission.branches.set(selected_branches)
                    
                    messages.success(request, f"User {user.username} updated successfully!")
                    return redirect("authentication:user_list")
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
        "all_branches": all_branches,
        "assigned_branches": assigned_branches,
    }
    return render(request, "authentication/edit_user.html", context)


@login_required
def edit_user_styled(request, user_id):
    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_edit_users"
    ):
        messages.error(request, "You do not have permission to edit users.")
        return redirect("dashboard:index")

    user_to_edit = get_object_or_404(User, id=user_id)
    
    # Get current business
    current_business = get_current_business()
    
    # Get all branches for this business
    all_branches = Branch.objects.filter(business=current_business) if current_business else Branch.objects.none()
    
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
                    
                    # Save or create user permissions
                    if hasattr(user_permission, 'id'):
                        permission = permission_form.save(commit=False)
                        permission.user = user
                        permission.save()
                        permission_form.save_m2m()  # Save many-to-many relationships
                    else:
                        permission = permission_form.save(commit=False)
                        permission.user = user
                        permission.save()
                        permission_form.save_m2m()  # Save many-to-many relationships
                    
                    # Handle branch assignments
                    if 'branches' in request.POST:
                        selected_branches = request.POST.getlist('branches')
                        permission.branches.set(selected_branches)
                    
                    messages.success(request, f"User {user.username} updated successfully!")
                    return redirect("authentication:user_list")
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
        "all_branches": all_branches,
        "assigned_branches": assigned_branches,
    }
    return render(request, "authentication/edit_user_styled.html", context)


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, "Your password was successfully updated!")
            return redirect("dashboard:index")
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "authentication/change_password.html", {"form": form})


def check_user_permission(user, permission_type):
    """
    Check if a user has a specific permission.
    """
    # Account owners have access to everything
    if user.role.lower() == "admin":
        return True

    try:
        # Get user permissions
        user_permission = UserPermission.objects.get(user=user)

        # Check if user has the specific permission
        if permission_type == "can_create":
            return user_permission.can_create
        elif permission_type == "can_edit":
            return user_permission.can_edit
        elif permission_type == "can_delete":
            return user_permission.can_delete
        elif permission_type == "can_access_products":
            return user_permission.can_access_products
        elif permission_type == "can_access_sales":
            return user_permission.can_access_sales
        elif permission_type == "can_access_purchases":
            return user_permission.can_access_purchases
        elif permission_type == "can_access_customers":
            return user_permission.can_access_customers
        elif permission_type == "can_access_suppliers":
            return user_permission.can_access_suppliers
        elif permission_type == "can_access_expenses":
            return user_permission.can_access_expenses
        elif permission_type == "can_access_reports":
            return user_permission.can_access_reports
        elif permission_type == "can_access_settings":
            return user_permission.can_access_settings
        elif permission_type == "can_manage_users":
            return user_permission.can_manage_users
        elif permission_type == "can_create_users":
            return user_permission.can_create_users
        elif permission_type == "can_edit_users":
            return user_permission.can_edit_users
        elif permission_type == "can_delete_users":
            return user_permission.can_delete_users
        else:
            # Default to False for unknown permissions
            return False
    except UserPermission.DoesNotExist:
        # If no custom permissions exist, default to False for edit/delete actions
        # but True for view actions
        if permission_type in [
            "can_create",
            "can_edit",
            "can_delete",
            "can_manage_users",
            "can_create_users",
            "can_edit_users",
            "can_delete_users",
        ]:
            return False
        else:
            return True


@login_required
def create_business_view(request):
    """Handle business creation for logged-in users"""
    # Check if user already has a business
    if request.user.owned_businesses.exists():
        messages.info(request, "You already have a business registered.")
        return redirect("dashboard:index")
    
    if request.method == "POST":
        company_name = request.POST.get("company_name")
        email = request.POST.get("email")
        
        if company_name and email:
            try:
                # Create business with pending status
                business = Business.objects.create(
                    company_name=company_name,
                    email=email,
                    owner=request.user,
                    plan_type="free",
                    status="pending"  # Set to pending by default
                )
                
                # Send email notification to business owner
                send_business_creation_email(request, business)
                
                messages.success(request, "Business created successfully! Your business is pending approval by an administrator.")
                return redirect("dashboard:index")
            except Exception as e:
                messages.error(request, f"Error creating business: {str(e)}")
        else:
            messages.error(request, "Please fill in all required fields.")
    
    return render(request, "authentication/create_business.html")


def send_business_creation_email(request, business):
    """Send email notification about business creation"""
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
        
        # Check if business owner has an email
        if not business.owner or not business.owner.email:
            return  # No email to send to
            
        # Prepare email context
        context = {
            "business": business,
            "business_settings": business_settings,
            "owner": business.owner,
            "login_url": request.build_absolute_uri("/accounts/login/"),
            "current_year": timezone.now().year,
        }
        
        # Render email templates
        subject = f"[{business_settings.business_name}] Business Creation Confirmation"
        html_message = render_to_string("emails/business_registration.html", context)
        plain_message = render_to_string("emails/business_registration.txt", context)
        
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
        logger.error(f"Failed to send business creation email: {str(e)}")

def register_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful. You can now log in.')
            return redirect('authentication:login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'authentication/register.html', {'form': form})

